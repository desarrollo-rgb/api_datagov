"""Punto de entrada de la API DataGov."""

from fastapi import FastAPI

from app.api import comentarios, datasets, health
from app.errors import registrar_manejadores_errores

app = FastAPI(
    title="API DataGov",
    version="0.1.0",
)

# Conecta los manejadores de error: ante un fallo, respuestas HTTP limpias y consistentes.
registrar_manejadores_errores(app)

# Endpoints publicos de salud (para la infraestructura).
app.include_router(health.router)
# Endpoints de datos (protegidos por token).
app.include_router(datasets.router)
# Endpoint de comentarios de ValleData, para el DAG (protegido por token).
app.include_router(comentarios.router)
