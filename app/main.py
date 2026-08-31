"""Punto de entrada de la API DataGov."""

from fastapi import FastAPI

app = FastAPI(
    title="API DataGov",
    version="0.1.0",
)


@app.get("/")
async def hola_mundo() -> dict[str, str]:
    return {"mensaje": "Hola mundo"}
