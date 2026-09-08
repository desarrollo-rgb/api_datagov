"""Acceso de solo lectura a los datos del modelo de rendimiento.

Mismo patron que `agricultura_repo`: UNA interfaz (`RendimientoRepo`) y DOS formas de
cumplirla:

- `RendimientoRepoFalso`    -> datos de ejemplo en memoria. No toca BigQuery.
- `RendimientoRepoBigQuery` -> consulta real a la tabla `gold_modelo_rendimiento`.

Los endpoints solo conocen la interfaz; la eleccion la hace `get_rendimiento_repo()` segun
la configuracion (`usar_datos_falsos`). Pasar de datos inventados a reales es cambiar UNA
variable de entorno, sin tocar la logica.
"""

from typing import Protocol

from app.config import get_settings


class RendimientoRepo(Protocol):
    """Contrato: cualquier repositorio de rendimiento sabe entregar filas."""

    def obtener_filas(self, limite: int) -> list[dict]:
        ...


class RendimientoRepoFalso:
    """Datos de ejemplo, para desarrollar sin credenciales ni tabla reales.

    Las columnas imitan la tabla real `gold_modelo_rendimiento`, para que cuando llegue
    BigQuery el resto de la app no note el cambio.
    """

    _FILAS_EJEMPLO: list[dict] = [
        {"anio": 2000, "municipio": "bolivar", "cultivo": "papaya", "rendimiento_toneladas_ha": 16.0, "promedio_oni": -0.825},
        {"anio": 2001, "municipio": "cerrito", "cultivo": "caña", "rendimiento_toneladas_ha": 82.5, "promedio_oni": 0.4},
        {"anio": 2002, "municipio": "palmira", "cultivo": "maíz", "rendimiento_toneladas_ha": 5.3, "promedio_oni": -0.1},
    ]

    def obtener_filas(self, limite: int) -> list[dict]:
        return self._FILAS_EJEMPLO[:limite]


class RendimientoRepoBigQuery:
    """Consulta real de solo lectura a la tabla de rendimiento en BigQuery."""

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
        tabla = f"`{s.gcp_project_id}.{s.bigquery_dataset}.{s.bigquery_tabla_gold_modelo_rendimiento}`"
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


def get_rendimiento_repo() -> RendimientoRepo:
    """Decide que repositorio usar segun la configuracion.

    Sirve tambien como dependencia de FastAPI: los endpoints la reciben con `Depends`
    y en las pruebas se puede sustituir por una version falsa.
    """
    if get_settings().usar_datos_falsos:
        return RendimientoRepoFalso()
    return RendimientoRepoBigQuery()
