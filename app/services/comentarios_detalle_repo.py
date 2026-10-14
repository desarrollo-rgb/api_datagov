"""Acceso de solo lectura al DETALLE de comentarios analizados.

Mismo patron que los demas repos: UNA interfaz (`ComentariosDetalleRepo`) y DOS formas
de cumplirla:

- `ComentariosDetalleRepoFalso`    -> datos de ejemplo en memoria. No toca BigQuery.
- `ComentariosDetalleRepoBigQuery` -> consulta real a la VISTA
  `valledata_api_comentarios_detalle` (dataset `gold_valledata`).

Es el resultado de la analitica que hace el DAG/Composer sobre los comentarios de CKAN:
un comentario por fila, ya con su sentimiento y emocion. Esta API solo lo expone.

Filtros opcionales:
- `fecha_hora_publicacion` (datetime): trae los publicados DESDE esa fecha/hora en
  adelante (fecha_hora_publicacion >= valor).
- `municipio` (str en MAYUSCULA): trae solo los de ese municipio.
"""

from datetime import datetime, timezone
from typing import Protocol

from app.config import get_settings


def _a_utc_naive(dt: datetime) -> datetime:
    """Normaliza a UTC sin zona, para comparar fechas con y sin zona de forma consistente."""
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _fecha_es_mayor_o_igual(fecha_iso: str | None, desde: datetime) -> bool:
    """True si `fecha_iso` (string ISO) es >= `desde`. Si no se puede parsear, la incluye."""
    try:
        dt = datetime.fromisoformat(fecha_iso)  # type: ignore[arg-type]
    except (ValueError, TypeError):
        return True
    return _a_utc_naive(dt) >= desde


class ComentariosDetalleRepo(Protocol):
    """Contrato: cualquier repositorio de detalle sabe entregar filas (con filtros)."""

    def obtener_filas(
        self,
        limite: int | None,
        fecha_hora_publicacion: datetime | None = None,
        municipio: str | None = None,
    ) -> list[dict]:
        ...


class ComentariosDetalleRepoFalso:
    """Datos de ejemplo, con las mismas columnas que la vista real."""

    _FILAS_EJEMPLO: list[dict] = [
        {
            "id_comentario": "ALCALA-144",
            "fecha_publicacion": "2026-10-10",
            "fecha_hora_publicacion": "2026-10-10T14:33:32.436942",
            "id_municipio_dataset": "ALCALA-0A4D4537-31B3-42F5-A9D6-6054C2710739",
            "municipio": "ALCALA",
            "dataset_id": "0A4D4537-31B3-42F5-A9D6-6054C2710739",
            "nombre_dataset": "CONJUNTO DE DATOS 1 OCTUBRE 07",
            "sentimiento": "NEGATIVO",
            "emocion": "FRUSTRACION",
            "texto_es": "EL ENLACE DE DESCARGA DEL RECURSO CSV MARCA UN ERROR 404 Y NO PERMITE BAJAR LA INFORMACION.",
        },
        {
            "id_comentario": "ALCALA-143",
            "fecha_publicacion": "2026-10-10",
            "fecha_hora_publicacion": "2026-10-10T14:33:07.879329",
            "id_municipio_dataset": "ALCALA-0A4D4537-31B3-42F5-A9D6-6054C2710739",
            "municipio": "ALCALA",
            "dataset_id": "0A4D4537-31B3-42F5-A9D6-6054C2710739",
            "nombre_dataset": "CONJUNTO DE DATOS 1 OCTUBRE 07",
            "sentimiento": "NEUTRO",
            "emocion": "NEUTRAL",
            "texto_es": "¿ALGUIEN SABE CON QUE FRECUENCIA PLANEAN ACTUALIZAR ESTE CONJUNTO DE DATOS EN LA PLATAFORMA?",
        },
    ]

    def obtener_filas(
        self,
        limite: int | None,
        fecha_hora_publicacion: datetime | None = None,
        municipio: str | None = None,
    ) -> list[dict]:
        filas = self._FILAS_EJEMPLO
        if municipio is not None:
            filas = [f for f in filas if str(f["municipio"]).upper() == municipio]
        if fecha_hora_publicacion is not None:
            filas = [
                f for f in filas
                if _fecha_es_mayor_o_igual(f.get("fecha_hora_publicacion"), fecha_hora_publicacion)
            ]
        return filas[:limite]


class ComentariosDetalleRepoBigQuery:
    """Consulta real de solo lectura a la vista de detalle en BigQuery."""

    def __init__(self) -> None:
        import os

        from google.cloud import bigquery

        self._settings = get_settings()

        # En local, la libreria de Google necesita saber donde esta la llave.
        # En Cloud Run / GKE esta variable va vacia y se usa la SA del servicio.
        if self._settings.google_application_credentials:
            os.environ.setdefault(
                "GOOGLE_APPLICATION_CREDENTIALS",
                self._settings.google_application_credentials,
            )

        self._client = bigquery.Client(project=self._settings.gcp_project_id)

    def obtener_filas(
        self,
        limite: int | None,
        fecha_hora_publicacion: datetime | None = None,
        municipio: str | None = None,
    ) -> list[dict]:
        from google.cloud import bigquery

        s = self._settings

        # El NOMBRE de la vista viene de la configuracion (fuente confiable); los VALORES
        # que envia el consumidor (municipio, fecha, limite) van SIEMPRE como parametros,
        # nunca concatenados: asi se evita la inyeccion SQL.
        tabla = f"`{s.gcp_project_id}.{s.bigquery_dataset_comentarios}.{s.bigquery_vista_comentarios_detalle}`"

        condiciones: list[str] = []
        parametros: list = []
        if municipio is not None:
            condiciones.append("UPPER(municipio) = @municipio")
            parametros.append(bigquery.ScalarQueryParameter("municipio", "STRING", municipio))
        if fecha_hora_publicacion is not None:
            # CAST a DATETIME para comparar sin importar si la columna es DATETIME, TIMESTAMP
            # o STRING. El valor va como DATETIME (sin zona, normalizado a UTC).
            condiciones.append("CAST(fecha_hora_publicacion AS DATETIME) >= @fecha")
            parametros.append(
                bigquery.ScalarQueryParameter("fecha", "DATETIME", fecha_hora_publicacion)
            )

        where = (" WHERE " + " AND ".join(condiciones)) if condiciones else ""
        consulta = f"SELECT * FROM {tabla}{where}"
        if limite is not None:
            consulta += " LIMIT @limite"
            parametros.append(bigquery.ScalarQueryParameter("limite", "INT64", limite))

        configuracion = bigquery.QueryJobConfig(query_parameters=parametros)
        from app.services.bigquery_util import ejecutar_consulta

        return ejecutar_consulta(self._client, consulta, configuracion)


def get_comentarios_detalle_repo() -> ComentariosDetalleRepo:
    """Decide que repositorio usar segun la configuracion.

    Sirve tambien como dependencia de FastAPI: los endpoints la reciben con `Depends`
    y en las pruebas se puede sustituir por una version falsa.
    """
    if get_settings().usar_datos_falsos:
        return ComentariosDetalleRepoFalso()
    return ComentariosDetalleRepoBigQuery()
