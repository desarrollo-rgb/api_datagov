"""Configuracion central de la API, leida desde variables de entorno.

Regla de oro: nada de valores fijos ni secretos escritos en el codigo. Todo lo que
cambia entre entornos (local, pruebas, produccion) entra por aqui, desde el archivo
`.env` o desde las variables de entorno del contenedor.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Lee las variables desde un archivo .env si existe. `extra="ignore"` evita que
    # una variable de mas en el entorno rompa el arranque.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Seguridad ---
    # Token que debe presentar quien consume la API (por ahora, la API ValleData).
    # No tiene valor por defecto A PROPOSITO: si falta, la app no arranca. Es preferible
    # fallar al arrancar que quedar sin proteccion por un olvido.
    api_token: str

    # --- Limites de consulta ---
    # Rango permitido para el parametro `limite`, y si se permite el "full select"
    # (traer todo sin limite). Configurables por entorno; cambiarlos solo requiere reiniciar.
    limite_minimo_select: int = 1
    limite_maximo_select: int = 1000000
    # True  -> sin `limite` se devuelven TODAS las filas.
    # False -> sin `limite` se topa en LIMITE_MAXIMO_SELECT.
    permitir_full_select: bool = True

    # --- Modo de datos ---
    # True  -> responde con datos de ejemplo, sin tocar BigQuery (para desarrollar).
    # False -> consulta BigQuery de verdad (cuando ya tengas credenciales y tabla).
    usar_datos_falsos: bool = True

    # --- Identidad y ubicacion en GCP ---
    gcp_project_id: str = "proyecto-dummy"
    bigquery_dataset: str = "agricultura_dataset"
    bigquery_tabla_gold_cultivos_valle_geo: str = "gold_cultivos_valle_geo"
    bigquery_tabla_gold_modelo_rendimiento: str = "gold_modelo_rendimiento"
    bigquery_tabla_gold_pronostico_produccion: str = "gold_pronostico_produccion"
    bigquery_tabla_gold_comentarios_sentimiento: str = "gold_comentarios_sentimiento"

    # Ruta al archivo de llave de la service account (solo para desarrollo local).
    # En Cloud Run / GKE se deja vacia: la identidad la aporta la SA del servicio.
    google_application_credentials: str | None = None

    # --- Cliente hacia la API ValleData (Flujo 2: ingesta de comentarios) ---
    # True  -> comentarios de ejemplo, sin llamar a ValleData (para desarrollar).
    # False -> llama a la API ValleData real.
    usar_valledata_falso: bool = True
    valledata_api_base_url: str = "http://localhost:8001"
    valledata_api_token: str = "token-dummy-valledata-no-usar-en-produccion"
    valledata_timeout_segundos: int = 30


@lru_cache
def get_settings() -> Settings:
    """Devuelve la configuracion una sola vez (cacheada) para toda la aplicacion."""
    return Settings()
