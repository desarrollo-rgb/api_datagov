"""Endpoint que expone los comentarios de ValleData (Flujo 2: para el DAG).

DataGov obtiene los comentarios desde la API ValleData y los deja disponibles aqui. El
DAG de analitica consume ESTE endpoint, no la API ValleData directamente: asi el DAG solo
conoce a DataGov y no se acopla al otro proyecto.

Los comentarios son datos de ciudadanos, por eso el endpoint esta protegido con token.
"""

from fastapi import APIRouter, Depends

from app.security import verificar_token
from app.services.valledata_client import ClienteValleData, get_cliente_valledata

router = APIRouter(
    prefix="/api/v1/bd_ckan",
    tags=["bases de datos ckan"],
    dependencies=[Depends(verificar_token)],
)


@router.get("/comments")
async def listar_comentarios(
    cliente: ClienteValleData = Depends(get_cliente_valledata),
) -> dict:
    """Devuelve los comentarios que DataGov obtuvo de ValleData, hechos a los recursos de los conjuntos de datos de los portales ckan de los 14 municipios del proyecto, con la lista de municipios que fallaron."""
    comentarios, municipios_con_error = cliente.obtener_comentarios()
    return {
        "comentarios": comentarios,
        "total": len(comentarios),
        "municipios_con_error": municipios_con_error,
    }
