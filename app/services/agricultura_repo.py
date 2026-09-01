"""Acceso de solo lectura a los datos de 'agricultura'.

Aqui vive el truco central: definimos UNA interfaz (`AgriculturaRepo`) y DOS formas
de cumplirla:

- `AgriculturaRepoFalso`   -> datos de ejemplo en memoria. No toca BigQuery.
- `AgriculturaRepoBigQuery`-> consulta real a BigQuery.

El resto de la aplicacion (los endpoints) solo conoce la interfaz; nunca sabe cual de
las dos esta usando. La eleccion la hace `get_agricultura_repo()` mirando la
configuracion (`usar_datos_falsos`). Por eso, pasar de datos inventados a datos reales
es cambiar UNA variable de entorno, sin tocar la logica.
"""

from typing import Protocol

from app.config import get_settings


class AgriculturaRepo(Protocol):
    """Contrato: cualquier repositorio de agricultura sabe entregar filas."""

    def obtener_filas(self, limite: int) -> list[dict]:
        ...


class AgriculturaRepoFalso:
    """Datos de ejemplo, para desarrollar sin credenciales ni tabla reales.

    Las columnas imitan como se veria la tabla real, para que cuando llegue BigQuery
    el resto de la app no note el cambio.
    """

    _FILAS_EJEMPLO: list[dict] = [
        {"municipio": "Alcalá", "cultivo": "café", "area_hectareas": 1200, "produccion_toneladas": 980, "anio": 2026},
        {"municipio": "Cerrito", "cultivo": "caña", "area_hectareas": 3400, "produccion_toneladas": 25600, "anio": 2026},
        {"municipio": "Guacarí", "cultivo": "maíz", "area_hectareas": 850, "produccion_toneladas": 4200, "anio": 2026},
        {"municipio": "Pradera", "cultivo": "plátano", "area_hectareas": 640, "produccion_toneladas": 7300, "anio": 2026},
        {"municipio": "Yotoco", "cultivo": "aguacate", "area_hectareas": 410, "produccion_toneladas": 3100, "anio": 2026},
    ]

    def obtener_filas(self, limite: int) -> list[dict]:
        return self._FILAS_EJEMPLO[:limite]


class AgriculturaRepoBigQuery:
    """Consulta real de solo lectura a la tabla de agricultura en BigQuery."""

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

        # El NOMBRE de la tabla viene de nuestra configuracion (fuente confiable),
        # por eso se puede interpolar. En cambio, los VALORES que podria enviar un
        # consumidor (como `limite`) van SIEMPRE como parametros, nunca concatenados:
        # asi se evita la inyeccion SQL.
        tabla = f"`{s.gcp_project_id}.{s.bigquery_dataset}.{s.bigquery_tabla_agricultura}`"
        consulta = f"""
            SELECT municipio, cultivo, area_hectareas, produccion_toneladas, anio
            FROM {tabla}
            LIMIT @limite
        """
        configuracion = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("limite", "INT64", limite),
            ]
        )
        resultado = self._client.query(consulta, job_config=configuracion).result()
        return [dict(fila) for fila in resultado]


def get_agricultura_repo() -> AgriculturaRepo:
    """Decide que repositorio usar segun la configuracion.

    Sirve tambien como dependencia de FastAPI: los endpoints la reciben con `Depends`
    y en las pruebas se puede sustituir por una version falsa.
    """
    if get_settings().usar_datos_falsos:
        return AgriculturaRepoFalso()
    return AgriculturaRepoBigQuery()
