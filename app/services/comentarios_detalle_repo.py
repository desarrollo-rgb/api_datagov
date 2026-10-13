"""Acceso de solo lectura al DETALLE de comentarios analizados.

Mismo patron que los demas repos: UNA interfaz (`ComentariosDetalleRepo`) y DOS formas
de cumplirla:

- `ComentariosDetalleRepoFalso`    -> datos de ejemplo en memoria. No toca BigQuery.
- `ComentariosDetalleRepoBigQuery` -> consulta real a la VISTA
  `valledata_api_comentarios_detalle` (dataset `gold_valledata`).

Es el resultado de la analitica que hace el DAG/Composer sobre los comentarios de CKAN:
un comentario por fila, ya con su sentimiento y emocion. Esta API solo lo expone.
"""

from typing import Protocol

from app.config import get_settings


class ComentariosDetalleRepo(Protocol):
    """Contrato: cualquier repositorio de detalle sabe entregar filas."""

    def obtener_filas(self, limite: int | None) -> list[dict]:
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

    def obtener_filas(self, limite: int | None) -> list[dict]:
        return self._FILAS_EJEMPLO[:limite]


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

    def obtener_filas(self, limite: int | None) -> list[dict]:
        from google.cloud import bigquery

        s = self._settings

        # La vista vive en el dataset de comentarios (gold_valledata), no en el dataset
        # principal. El NOMBRE viene de la configuracion (fuente confiable); el VALOR que
        # envia el consumidor (`limite`) va SIEMPRE como parametro: evita inyeccion SQL.
        tabla = f"`{s.gcp_project_id}.{s.bigquery_dataset_comentarios}.{s.bigquery_vista_comentarios_detalle}`"
        if limite is None:
            consulta = f"SELECT * FROM {tabla}"
            configuracion = bigquery.QueryJobConfig()
        else:
            consulta = f"SELECT * FROM {tabla} LIMIT @limite"
            configuracion = bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("limite", "INT64", limite)]
            )
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
