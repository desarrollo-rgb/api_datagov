"""Cliente hacia la API ValleData (Flujo 2: ValleData -> DataGov).

Mismo patron que el repositorio de BigQuery: UNA interfaz, DOS implementaciones.
- ClienteValleDataFalso: comentarios de ejemplo en memoria (para desarrollar sin ValleData).
- ClienteValleDataHTTP: llamadas HTTP reales a la API ValleData.

DataGov consume el comentario CRUDO que expone ValleData y lo reexpone tal cual para el
DAG. No lo clasifica (eso lo hace el DAG despues). La forma del comentario debe coincidir
con lo que ValleData entrega en `GET /api/v1/comentarios`.
"""

from datetime import datetime, timezone
from typing import Protocol

from app.config import get_settings
from app.models.schemas import Comentario


def _a_utc_naive(dt: datetime) -> datetime:
    """Normaliza a UTC sin zona, para comparar fechas con y sin zona de forma consistente."""
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _fecha_es_mayor_o_igual(fecha_iso: str, desde_iso: str) -> bool:
    """True si `fecha_iso` >= `desde_iso` (ambos strings ISO). Si no se pueden parsear, incluye."""
    try:
        f = datetime.fromisoformat(fecha_iso)
        d = datetime.fromisoformat(desde_iso)
    except (ValueError, TypeError):
        return True
    return _a_utc_naive(f) >= _a_utc_naive(d)


class ClienteValleData(Protocol):
    """Contrato: entrega los comentarios y la lista de municipios que fallaron.

    Devolvemos ambos (igual que ValleData) para que el DAG sepa si la data viene
    incompleta: si un municipio fallo en ValleData, sus comentarios no vienen, pero el
    resto si, y su nombre aparece en `municipios_con_error`.

    `desde` (fecha ISO 8601) se reenvia tal cual a ValleData para filtrar por fecha de
    creacion (created >= desde). Si es None, se traen todos.
    """

    def obtener_comentarios(self, desde: str | None = None) -> tuple[list[Comentario], list[str]]:
        ...


class ClienteValleDataFalso:
    """Comentarios de ejemplo, con la MISMA forma que expone ValleData de verdad."""

    _EJEMPLOS: list[dict] = [
        {"id": 1, "municipio": "alcala", "dataset_id": "d-100", "nombre_dataset": "Cultivos del Valle 2026", "usuario": "ana", "texto_es": "Buen conjunto de datos", "texto_en": "Good dataset", "fecha": "2026-08-20T10:00:00Z"},
        {"id": 2, "municipio": "alcala", "dataset_id": "d-100", "nombre_dataset": "Cultivos del Valle 2026", "usuario": "luis", "texto_es": "Faltan los datos de 2025", "texto_en": "2025 data is missing", "fecha": "2026-08-20T11:30:00Z"},
        {"id": 1, "municipio": "cerrito", "dataset_id": "d-200", "nombre_dataset": "Presupuesto municipal", "usuario": "sara", "texto_es": "Muy util, gracias", "texto_en": "Very useful, thanks", "fecha": "2026-08-21T09:15:00Z"},
        # Comentario anonimo: usuario=None, como llegan muchos de CKAN en la realidad.
        {"id": 1, "municipio": "guacari", "dataset_id": "d-300", "nombre_dataset": None, "usuario": None, "texto_es": "El archivo no abre", "texto_en": "The file won't open", "fecha": "2026-08-19T14:00:00Z"},
    ]

    def obtener_comentarios(self, desde: str | None = None) -> tuple[list[Comentario], list[str]]:
        comentarios = [Comentario(**c) for c in self._EJEMPLOS]
        if desde:
            comentarios = [c for c in comentarios if _fecha_es_mayor_o_igual(c.fecha, desde)]
        return comentarios, []  # ningun municipio con error en modo falso


class ClienteValleDataHTTP:
    """Implementacion real: obtiene los comentarios de ValleData por HTTP."""

    def __init__(self) -> None:
        import httpx

        s = get_settings()
        self._cliente = httpx.Client(
            base_url=s.valledata_api_base_url,
            headers={"Authorization": f"Bearer {s.valledata_api_token}"},
            timeout=s.valledata_timeout_segundos,
        )

    def obtener_comentarios(self, desde: str | None = None) -> tuple[list[Comentario], list[str]]:
        import httpx

        from app.errors import ErrorValleDataNoDisponible, ErrorValleDataRespuesta

        # Si viene `desde`, se lo reenviamos a ValleData tal cual para que filtre por fecha.
        params = {"desde": desde} if desde else {}
        try:
            respuesta = self._cliente.get("/api/v1/expose/bd_ckan/comments", params=params)
            respuesta.raise_for_status()
        except httpx.HTTPStatusError as e:
            # ValleData contesto, pero con 4xx/5xx (p. ej. token malo, o fallo interno).
            raise ErrorValleDataRespuesta(f"codigo {e.response.status_code}") from e
        except httpx.RequestError as e:
            # Ni siquiera se pudo contactar a ValleData (caido, timeout, DNS, red).
            raise ErrorValleDataNoDisponible(str(e)) from e

        # ValleData responde {"comentarios": [...], "total": N, "municipios_con_error": [...]}.
        # Propagamos ambos: los comentarios y que municipios fallaron.
        cuerpo = respuesta.json()
        comentarios = [Comentario.model_validate(item) for item in cuerpo["comentarios"]]
        municipios_con_error = cuerpo.get("municipios_con_error", [])
        return comentarios, municipios_con_error


def get_cliente_valledata() -> ClienteValleData:
    """Decide que cliente usar segun la configuracion.

    Sirve tambien como dependencia de FastAPI: los endpoints la reciben con `Depends`
    y en las pruebas se puede sustituir por una version falsa.
    """
    if get_settings().usar_valledata_falso:
        return ClienteValleDataFalso()
    return ClienteValleDataHTTP()
