"""Acceso de solo lectura a los datos de sentimiento de comentarios.

Mismo patron que los demas repos: UNA interfaz (`SentimientoRepo`) y DOS formas de
cumplirla:

- `SentimientoRepoFalso`    -> datos de ejemplo en memoria. No toca BigQuery.
- `SentimientoRepoBigQuery` -> consulta real a la tabla `gold_comentarios_sentimiento`.

Esta tabla ya trae el analisis de sentimiento procesado (lo hizo el DAG); esta API solo
lo expone. Los endpoints solo conocen la interfaz; la eleccion la hace
`get_sentimiento_repo()` segun la configuracion (`usar_datos_falsos`).
"""

from typing import Protocol

from app.config import get_settings


class SentimientoRepo(Protocol):
    """Contrato: cualquier repositorio de sentimiento sabe entregar filas."""

    def obtener_filas(self, limite: int) -> list[dict]:
        ...


class SentimientoRepoFalso:
    """Datos de ejemplo, para desarrollar sin credenciales ni tabla reales.

    Las columnas imitan la tabla real `gold_comentarios_sentimiento`, para que cuando
    llegue BigQuery el resto de la app no note el cambio.
    """

    _FILAS_EJEMPLO: list[dict] = [
        {"municipio": "alcala", "id_dataset": "c98cfd48-9281-1c92-984f-e323b3292925", "total_comentarios": 1, "positivos": 0, "negativos": 1, "neutros": 0, "confianza_promedio": 0.9141, "emocion_predominante": "NEG"},
        {"municipio": "cerrito", "id_dataset": "d753b231-dc4e-4ab4-a025-3e7000000000", "total_comentarios": 5, "positivos": 3, "negativos": 1, "neutros": 1, "confianza_promedio": 0.8123, "emocion_predominante": "POS"},
        {"municipio": "guacari", "id_dataset": "28ae3104-f5a0-43fa-9153-f27921d13796", "total_comentarios": 2, "positivos": 1, "negativos": 0, "neutros": 1, "confianza_promedio": 0.7456, "emocion_predominante": "NEU"},
    ]

    def obtener_filas(self, limite: int) -> list[dict]:
        return self._FILAS_EJEMPLO[:limite]


class SentimientoRepoBigQuery:
    """Consulta real de solo lectura a la tabla de sentimiento en BigQuery."""

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

    def obtener_filas(self, limite: int) -> list[dict]:
        from google.cloud import bigquery

        s = self._settings

        # El NOMBRE de la tabla viene de la configuracion (fuente confiable), por eso se
        # puede interpolar. El VALOR que envia el consumidor (`limite`) va SIEMPRE como
        # parametro, nunca concatenado: asi se evita la inyeccion SQL.
        tabla = f"`{s.gcp_project_id}.{s.bigquery_dataset}.{s.bigquery_tabla_gold_comentarios_sentimiento}`"
        consulta = f"""
            SELECT *
            FROM {tabla}
            LIMIT @limite
        """
        configuracion = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("limite", "INT64", limite),
            ]
        )
        from app.services.bigquery_util import ejecutar_consulta

        return ejecutar_consulta(self._client, consulta, configuracion)


def get_sentimiento_repo() -> SentimientoRepo:
    """Decide que repositorio usar segun la configuracion.

    Sirve tambien como dependencia de FastAPI: los endpoints la reciben con `Depends`
    y en las pruebas se puede sustituir por una version falsa.
    """
    if get_settings().usar_datos_falsos:
        return SentimientoRepoFalso()
    return SentimientoRepoBigQuery()
