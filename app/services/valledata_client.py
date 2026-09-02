"""Cliente hacia la API ValleData (Flujo 2: ValleData -> DataGov).

Mismo patron que el repositorio de BigQuery: UNA interfaz, DOS implementaciones.
- ClienteValleDataFalso: comentarios de ejemplo en memoria (para desarrollar sin ValleData).
- ClienteValleDataHTTP: llamadas HTTP reales a la API ValleData.

El contrato (ruta, campos) es PROVISIONAL: se ajustara cuando ValleData lo cierre. Como
todo vive tras esta interfaz, ese cambio no tocara los endpoints que sirven al DAG.
"""

from typing import Protocol

from app.config import get_settings
from app.models.schemas import Comentario


class ClienteValleData(Protocol):
    """Contrato: cualquier cliente de ValleData sabe entregar los comentarios."""

    def obtener_comentarios(self) -> list[Comentario]:
        ...


class ClienteValleDataFalso:
    """Comentarios de ejemplo, para desarrollar sin la API ValleData real."""

    _EJEMPLOS: list[dict] = [
        {"fecha": "2026-08-20T10:00:00Z", "comentario": "Buen conjunto de datos", "clasificacion": "positivo"},
        {"fecha": "2026-08-20T11:30:00Z", "comentario": "Faltan los datos de 2025", "clasificacion": "negativo"},
        {"fecha": "2026-08-21T09:15:00Z", "comentario": "Muy util, gracias", "clasificacion": "positivo"},
        {"fecha": "2026-08-21T16:45:00Z", "comentario": "Descargue el archivo sin problema", "clasificacion": "neutro"},
    ]

    def obtener_comentarios(self) -> list[Comentario]:
        return [Comentario(**c) for c in self._EJEMPLOS]


class ClienteValleDataHTTP:
    """Implementacion real: obtiene los comentarios de ValleData por HTTP.

    La ruta '/comentarios' y la forma de la respuesta son PROVISIONALES.
    """

    def __init__(self) -> None:
        import httpx

        s = get_settings()
        self._cliente = httpx.Client(
            base_url=s.valledata_api_base_url,
            headers={"Authorization": f"Bearer {s.valledata_api_token}"},
            timeout=s.valledata_timeout_segundos,
        )

    def obtener_comentarios(self) -> list[Comentario]:
        respuesta = self._cliente.get("/comentarios")
        respuesta.raise_for_status()
        return [Comentario.model_validate(item) for item in respuesta.json()]


def get_cliente_valledata() -> ClienteValleData:
    """Decide que cliente usar segun la configuracion.

    Sirve tambien como dependencia de FastAPI: los endpoints la reciben con `Depends`
    y en las pruebas se puede sustituir por una version falsa.
    """
    if get_settings().usar_valledata_falso:
        return ClienteValleDataFalso()
    return ClienteValleDataHTTP()
