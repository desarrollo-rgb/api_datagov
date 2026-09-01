"""Endpoints que exponen datos de la capa Gold (Parte 1: DataGov -> ValleData)."""

from fastapi import APIRouter, Depends, Query

from app.security import verificar_token
from app.services.agricultura_repo import AgriculturaRepo, get_agricultura_repo

# La dependencia va en el router: protege TODOS los endpoints de datasets de una vez.
router = APIRouter(
    prefix="/api/v1/datasets",
    tags=["datasets"],
    dependencies=[Depends(verificar_token)],
)


@router.get("/agricultura")
async def obtener_agricultura(
    limite: int = Query(default=100, ge=1, le=1000, description="Maximo de filas a devolver."),
    repo: AgriculturaRepo = Depends(get_agricultura_repo),
) -> dict:
    """Devuelve las filas de agricultura en formato tabular plano.

    El endpoint no sabe si los datos vienen de BigQuery o de ejemplos: eso lo resuelve
    `get_agricultura_repo()` segun la configuracion.
    """
    filas = repo.obtener_filas(limite=limite)
    return {
        "identificador": "agricultura",
        "filas": filas,
        "total_devuelto": len(filas),
    }
