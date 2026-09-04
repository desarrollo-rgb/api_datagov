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

    Las columnas imitan la tabla real `gold_cultivos_valle_geo` (las 27 columnas),
    para que cuando llegue BigQuery el resto de la app no note el cambio. Los valores
    son inventados pero con la forma y el tipo correctos.
    """

    _FILAS_EJEMPLO: list[dict] = [
        {
            "tipo_cultivo": "permanente", "anio": 2026, "semestre": 1.0,
            "codigo_municipio": 76248.0, "municipio": "El Cerrito",
            "latitud": 3.68, "longitud": -76.31, "altura_snm": 987.0,
            "temperatura_media": 24.5,
            "superficie_piso_calido_x": 12000.0, "superficie_piso_medio_x": 4500.0,
            "superficie_piso_frio_x": 800.0, "superficie_piso_paramo_x": 0.0,
            "codigo_cultivo": 101, "nombre_cultivo": "caña de azúcar",
            "hectareas_sembradas": 3400.0, "hectareas_cosechadas": 3200.0,
            "indice_oni": -0.5, "latitud_dec": 3.6845, "longitud_dec": -76.3112,
            "distancia_cavasa_km": 42.7, "wkt_geometry": "POINT(-76.3112 3.6845)",
            "piso_predominante": "cálido",
            "superficie_piso_calido_y": 12000.0, "superficie_piso_medio_y": 4500.0,
            "superficie_piso_frio_y": 800.0, "superficie_piso_paramo_y": 0.0,
        },
        {
            "tipo_cultivo": "permanente", "anio": 2026, "semestre": 1.0,
            "codigo_municipio": 76736.0, "municipio": "Sevilla",
            "latitud": 4.27, "longitud": -75.93, "altura_snm": 1580.0,
            "temperatura_media": 19.2,
            "superficie_piso_calido_x": 3000.0, "superficie_piso_medio_x": 9000.0,
            "superficie_piso_frio_x": 2500.0, "superficie_piso_paramo_x": 100.0,
            "codigo_cultivo": 202, "nombre_cultivo": "café",
            "hectareas_sembradas": 1200.0, "hectareas_cosechadas": 1150.0,
            "indice_oni": -0.5, "latitud_dec": 4.2712, "longitud_dec": -75.9345,
            "distancia_cavasa_km": 118.4, "wkt_geometry": "POINT(-75.9345 4.2712)",
            "piso_predominante": "medio",
            "superficie_piso_calido_y": 3000.0, "superficie_piso_medio_y": 9000.0,
            "superficie_piso_frio_y": 2500.0, "superficie_piso_paramo_y": 100.0,
        },
        {
            "tipo_cultivo": "transitorio", "anio": 2026, "semestre": 2.0,
            "codigo_municipio": 76520.0, "municipio": "Palmira",
            "latitud": 3.53, "longitud": -76.30, "altura_snm": 1001.0,
            "temperatura_media": 23.8,
            "superficie_piso_calido_x": 15000.0, "superficie_piso_medio_x": 3000.0,
            "superficie_piso_frio_x": 500.0, "superficie_piso_paramo_x": 0.0,
            "codigo_cultivo": 303, "nombre_cultivo": "maíz",
            "hectareas_sembradas": 850.0, "hectareas_cosechadas": 820.0,
            "indice_oni": -0.5, "latitud_dec": 3.5394, "longitud_dec": -76.3036,
            "distancia_cavasa_km": 25.1, "wkt_geometry": "POINT(-76.3036 3.5394)",
            "piso_predominante": "cálido",
            "superficie_piso_calido_y": 15000.0, "superficie_piso_medio_y": 3000.0,
            "superficie_piso_frio_y": 500.0, "superficie_piso_paramo_y": 0.0,
        },
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
        tabla = f"`{s.gcp_project_id}.{s.bigquery_dataset}.{s.bigquery_tabla_cultivos}`"
        # SELECT *: exponemos la tabla gold tal cual (todas sus columnas). Asi, si la
        # tabla cambia de columnas mas adelante, el endpoint las refleja sin tocar codigo.
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
