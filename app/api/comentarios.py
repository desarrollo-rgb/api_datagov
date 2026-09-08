"""Endpoint que expone los comentarios de ValleData (Flujo 2: para el DAG).

DataGov obtiene los comentarios desde la API ValleData y los deja disponibles aqui. El
DAG de analitica consume ESTE endpoint, no la API ValleData directamente: asi el DAG solo
conoce a DataGov y no se acopla al otro proyecto.

Los comentarios son datos de ciudadanos, por eso el endpoint esta protegido con token.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.security import verificar_token
from app.services.valledata_client import ClienteValleData, get_cliente_valledata

router = APIRouter(
    prefix="/api/v1/consume/bd_ckan",
    tags=["bases de datos ckan"],
    dependencies=[Depends(verificar_token)],
)


@router.get("/comments")
async def listar_comentarios(
    desde: str | None = Query(
        default=None,
        description=(
            "Fecha desde la cual traer comentarios (created >= desde). Acepta ISO 8601: "
            "fecha (2026-07-29) o fecha y hora (2026-07-29T23:58:33Z). "
            "Se reenvia a ValleData. Si se deja vacio, trae todos."
        ),
    ),
    cliente: ClienteValleData = Depends(get_cliente_valledata),
) -> dict:
    """Devuelve los comentarios que DataGov obtuvo de ValleData, hechos a los recursos de los conjuntos de datos de los portales ckan de los 14 municipios del proyecto, con la lista de municipios que fallaron. Se puede filtrar por fecha con el parametro `desde`."""
    _validar_desde(desde)
    comentarios, municipios_con_error = cliente.obtener_comentarios(desde=desde or None)
    return {
        "comentarios": comentarios,
        "total": len(comentarios),
        "municipios_con_error": municipios_con_error,
    }


def _validar_desde(valor: str | None) -> None:
    """Valida que `desde` sea una fecha ISO 8601. Si no, responde 422 (error de consumo).

    No transforma el valor: se reenvia tal cual a ValleData, que hace el filtrado real.
    """
    if valor is None or valor.strip() == "":
        return
    try:
        datetime.fromisoformat(valor)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Parametro 'desde' invalido. Usa ISO 8601, por ejemplo 2026-07-29 o 2026-07-29T23:58:33Z.",
        )
