"""Endpoint que expone los comentarios de ValleData (Flujo 2: para el DAG).

DataGov obtiene los comentarios desde la API ValleData y los deja disponibles aqui. El
DAG de analitica consume ESTE endpoint, no la API ValleData directamente: asi el DAG solo
conoce a DataGov y no se acopla al otro proyecto.

Los comentarios son datos de ciudadanos, por eso el endpoint esta protegido con token.
"""

from fastapi import APIRouter, Depends

from app.models.schemas import Comentario
from app.security import verificar_token
from app.services.valledata_client import ClienteValleData, get_cliente_valledata

router = APIRouter(
    prefix="/api/v1",
    tags=["comentarios"],
    dependencies=[Depends(verificar_token)],
)


@router.get("/comentarios")
async def listar_comentarios(
    cliente: ClienteValleData = Depends(get_cliente_valledata),
) -> dict:
    """Devuelve los comentarios que DataGov obtuvo de ValleData."""
    comentarios: list[Comentario] = cliente.obtener_comentarios()
    return {
        "comentarios": comentarios,
        "total": len(comentarios),
    }
