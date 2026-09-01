"""Punto de entrada de la API DataGov."""

from fastapi import FastAPI

from app.api import datasets, health

app = FastAPI(
    title="API DataGov",
    version="0.1.0",
)

# Endpoints publicos de salud (para la infraestructura).
app.include_router(health.router)
# Endpoints de datos (protegidos por token).
app.include_router(datasets.router)


@app.get("/")
async def hola_mundo() -> dict[str, str]:
    return {"mensaje": "Hola mundo"}
