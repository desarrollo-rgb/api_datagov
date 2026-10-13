"""Acceso de solo lectura al RESUMEN de comentarios por dataset.

Mismo patron que los demas repos: UNA interfaz (`ComentariosResumenRepo`) y DOS formas
de cumplirla:

- `ComentariosResumenRepoFalso`    -> datos de ejemplo en memoria. No toca BigQuery.
- `ComentariosResumenRepoBigQuery` -> consulta real a la VISTA
  `valledata_api_comentarios_resumen_dataset` (dataset `gold_valledata`).

Es el resultado de la analitica que hace el DAG/Composer: una fila por dataset, con los
totales y porcentajes agregados de sentimiento y emocion. Esta API solo lo expone.
"""

from typing import Protocol

from app.config import get_settings


class ComentariosResumenRepo(Protocol):
    """Contrato: cualquier repositorio de resumen sabe entregar filas."""

    def obtener_filas(self, limite: int | None) -> list[dict]:
        ...


class ComentariosResumenRepoFalso:
    """Datos de ejemplo, con las mismas columnas que la vista real."""

    _FILAS_EJEMPLO: list[dict] = [
        {
            "id_municipio_dataset": "ALCALA-CCE62EAC-EEA9-4865-A805-6899CA472B0F",
            "municipio": "ALCALA",
            "dataset_id": "CCE62EAC-EEA9-4865-A805-6899CA472B0F",
            "nombre_dataset": "AGRICULTURA DRP",
            "total_comentarios": 6,
            "comentarios_analizados": 6,
            "positivos": 1,
            "negativos": 3,
            "neutros": 2,
            "porcentaje_positivos": 0.1667,
            "porcentaje_negativos": 0.5,
            "porcentaje_neutros": 0.3333,
            "indice_sentimiento": -0.3333,
            "sentimiento_predominante": "NEGATIVO",
            "frustracion": 4,
            "enojo": 0,
            "disgusto": 0,
            "miedo": 0,
            "tristeza": 0,
            "sorpresa": 0,
            "confianza": 0,
            "gratitud": 0,
            "alegria": 1,
            "neutral": 1,
            "emocion_predominante": "FRUSTRACION",
            "porcentaje_emocion_predominante": 0.6667,
            "fecha_primer_comentario": "2026-10-10 19:05:49.703462 UTC",
            "fecha_ultimo_comentario": "2026-10-10 19:39:16.245583 UTC",
            "comentarios_ultimos_30_dias": 6,
            "fecha_ultimo_analisis": "2026-10-11 03:45:12.805387 UTC",
        },
        {
            "id_municipio_dataset": "ALCALA-44AA281F-E161-447C-9820-4B5B30FEA30A",
            "municipio": "ALCALA",
            "dataset_id": "44AA281F-E161-447C-9820-4B5B30FEA30A",
            "nombre_dataset": "CONJUNTO AGRICULTURA OCTUBRE 2",
            "total_comentarios": 5,
            "comentarios_analizados": 5,
            "positivos": 1,
            "negativos": 4,
            "neutros": 0,
            "porcentaje_positivos": 0.2,
            "porcentaje_negativos": 0.8,
            "porcentaje_neutros": 0.0,
            "indice_sentimiento": -0.6,
            "sentimiento_predominante": "NEGATIVO",
            "frustracion": 4,
            "enojo": 0,
            "disgusto": 0,
            "miedo": 0,
            "tristeza": 0,
            "sorpresa": 0,
            "confianza": 0,
            "gratitud": 0,
            "alegria": 1,
            "neutral": 0,
            "emocion_predominante": "FRUSTRACION",
            "porcentaje_emocion_predominante": 0.8,
            "fecha_primer_comentario": "2026-10-10 19:06:35.635073 UTC",
            "fecha_ultimo_comentario": "2026-10-10 19:40:09.016836 UTC",
            "comentarios_ultimos_30_dias": 5,
            "fecha_ultimo_analisis": "2026-10-11 03:45:12.805387 UTC",
        },
    ]

    def obtener_filas(self, limite: int | None) -> list[dict]:
        return self._FILAS_EJEMPLO[:limite]


class ComentariosResumenRepoBigQuery:
    """Consulta real de solo lectura a la vista de resumen en BigQuery."""

    def __init__(self) -> None:
        import os

        from google.cloud import bigquery

        self._settings = get_settings()

        if self._settings.google_application_credentials:
            os.environ.setdefault(
                "GOOGLE_APPLICATION_CREDENTIALS",
                self._settings.google_application_credentials,
            )

        self._client = bigquery.Client(project=self._settings.gcp_project_id)

    def obtener_filas(self, limite: int | None) -> list[dict]:
        from google.cloud import bigquery

        s = self._settings

        # La vista vive en el dataset de comentarios (gold_valledata). El NOMBRE viene de
        # la configuracion; el VALOR `limite` va SIEMPRE como parametro: evita inyeccion.
        tabla = f"`{s.gcp_project_id}.{s.bigquery_dataset_comentarios}.{s.bigquery_vista_comentarios_resumen_dataset}`"
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


def get_comentarios_resumen_repo() -> ComentariosResumenRepo:
    """Decide que repositorio usar segun la configuracion.

    Sirve tambien como dependencia de FastAPI: los endpoints la reciben con `Depends`
    y en las pruebas se puede sustituir por una version falsa.
    """
    if get_settings().usar_datos_falsos:
        return ComentariosResumenRepoFalso()
    return ComentariosResumenRepoBigQuery()
