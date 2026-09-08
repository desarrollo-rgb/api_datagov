"""Acceso de solo lectura a los datos del pronostico de produccion.

Mismo patron que los demas repos: UNA interfaz (`PronosticoRepo`) y DOS formas de
cumplirla:

- `PronosticoRepoFalso`    -> datos de ejemplo en memoria. No toca BigQuery.
- `PronosticoRepoBigQuery` -> consulta real a la tabla `gold_pronostico_produccion`.

Los endpoints solo conocen la interfaz; la eleccion la hace `get_pronostico_repo()` segun
la configuracion (`usar_datos_falsos`). Pasar de datos inventados a reales es cambiar UNA
variable de entorno, sin tocar la logica.
"""

from typing import Protocol

from app.config import get_settings


class PronosticoRepo(Protocol):
    """Contrato: cualquier repositorio de pronostico sabe entregar filas."""

    def obtener_filas(self, limite: int) -> list[dict]:
        ...


class PronosticoRepoFalso:
    """Datos de ejemplo, para desarrollar sin credenciales ni tabla reales.

    Las columnas imitan la tabla real `gold_pronostico_produccion`, para que cuando llegue
    BigQuery el resto de la app no note el cambio.
    """

    _FILAS_EJEMPLO: list[dict] = [
        {"id_municipio": 76001, "id_cultivo": 10214, "fecha_proyectada": "2020-01-01T00:00:00Z", "produccion_estimada": 12.333333333333332, "limite_inferior": 4.823781028612802, "limite_superior": 19.842885638053861},
        {"id_municipio": 76001, "id_cultivo": 10214, "fecha_proyectada": "2020-02-01T00:00:00Z", "produccion_estimada": 13.1, "limite_inferior": 5.4, "limite_superior": 20.8},
        {"id_municipio": 76109, "id_cultivo": 10322, "fecha_proyectada": "2020-01-01T00:00:00Z", "produccion_estimada": 8.75, "limite_inferior": 2.1, "limite_superior": 15.4},
    ]

    def obtener_filas(self, limite: int) -> list[dict]:
        return self._FILAS_EJEMPLO[:limite]


class PronosticoRepoBigQuery:
    """Consulta real de solo lectura a la tabla de pronostico en BigQuery."""

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
        tabla = f"`{s.gcp_project_id}.{s.bigquery_dataset}.{s.bigquery_tabla_gold_pronostico_produccion}`"
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


def get_pronostico_repo() -> PronosticoRepo:
    """Decide que repositorio usar segun la configuracion.

    Sirve tambien como dependencia de FastAPI: los endpoints la reciben con `Depends`
    y en las pruebas se puede sustituir por una version falsa.
    """
    if get_settings().usar_datos_falsos:
        return PronosticoRepoFalso()
    return PronosticoRepoBigQuery()
