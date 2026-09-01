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

    # --- Modo de datos ---
    # True  -> responde con datos de ejemplo, sin tocar BigQuery (para desarrollar).
    # False -> consulta BigQuery de verdad (cuando ya tengas credenciales y tabla).
    usar_datos_falsos: bool = True

    # --- Identidad y ubicacion en GCP ---
    gcp_project_id: str = "proyecto-dummy"
    bigquery_dataset: str = "agricultura_dataset"
    bigquery_tabla_agricultura: str = "agricultura"

    # Ruta al archivo de llave de la service account (solo para desarrollo local).
    # En Cloud Run / GKE se deja vacia: la identidad la aporta la SA del servicio.
    google_application_credentials: str | None = None


@lru_cache
def get_settings() -> Settings:
    """Devuelve la configuracion una sola vez (cacheada) para toda la aplicacion."""
    return Settings()
