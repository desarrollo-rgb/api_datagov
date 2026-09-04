"""Endpoints que exponen datos de la capa Gold (Parte 1: DataGov -> ValleData)."""

from fastapi import APIRouter, Depends, Query

from app.security import verificar_token
from app.services.agricultura_repo import AgriculturaRepo, get_agricultura_repo

# La dependencia va en el router: protege TODOS los endpoints de datasets de una vez.
router = APIRouter(
    prefix="/api/v1/dataset_valledata",
    tags=["dataset Valledata"],
    dependencies=[Depends(verificar_token)],
)


@router.get(
    "/gold_cultivos_valle_geo",
    summary="Obtener información de la tabla de cultivos",
)
async def obtener_agricultura(
    limite: int = Query(default=100, ge=1, le=1000, description="Maximo de filas a devolver."),
    repo: AgriculturaRepo = Depends(get_agricultura_repo),
) -> dict:
    """Devuelve los datos de cultivos de la tabla gold_cultivos_valle_geo en BigQuery."""
    # El endpoint no sabe si los datos vienen de BigQuery o de ejemplos: eso lo resuelve
    # get_agricultura_repo() segun la configuracion.
    filas = repo.obtener_filas(limite=limite)
    return {
        "identificador": "agricultura",
        "filas": filas,
        "total_devuelto": len(filas),
    }
