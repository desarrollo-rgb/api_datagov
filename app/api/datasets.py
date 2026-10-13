"""Endpoints que exponen las vistas de la analitica de comentarios (DataGov -> ValleData).

Las vistas viven en el dataset `gold_valledata`, por eso su URL usa ese nombre de dataset.
"""

from fastapi import APIRouter, Depends, Query

from app.security import verificar_token
from app.services.comentarios_detalle_repo import (
    ComentariosDetalleRepo,
    get_comentarios_detalle_repo,
)
from app.services.comentarios_resumen_repo import (
    ComentariosResumenRepo,
    get_comentarios_resumen_repo,
)

# La dependencia va en el router: protege TODOS los endpoints de una vez.
router = APIRouter(
    prefix="/api/v1/expose/gold_valledata",
    tags=["dataset Valledata"],
    dependencies=[Depends(verificar_token)],
)

# Parametro `limite`: opcional. Vacio = todas las filas; con valor = tope de filas.
_LIMITE = Query(
    default=None,
    ge=1,
    description="Maximo de filas a devolver. Vacio = todas.",
)


@router.get(
    "/valledata_api_comentarios_detalle",
    summary="Obtener el detalle de comentarios analizados",
)
async def obtener_comentarios_detalle(
    limite: int | None = _LIMITE,
    repo: ComentariosDetalleRepo = Depends(get_comentarios_detalle_repo),
) -> dict:
    """Devuelve el detalle de comentarios ya analizados (un comentario por fila, con su sentimiento y emoción) de la vista valledata_api_comentarios_detalle en BigQuery."""
    filas = repo.obtener_filas(limite=limite)
    return {
        "identificador": "comentarios_detalle",
        "filas": filas,
        "total_devuelto": len(filas),
    }


@router.get(
    "/valledata_api_comentarios_resumen_dataset",
    summary="Obtener el resumen de comentarios por dataset",
)
async def obtener_comentarios_resumen_dataset(
    limite: int | None = _LIMITE,
    repo: ComentariosResumenRepo = Depends(get_comentarios_resumen_repo),
) -> dict:
    """Devuelve el resumen de comentarios por dataset (totales y porcentajes de sentimiento y emoción) de la vista valledata_api_comentarios_resumen_dataset en BigQuery."""
    filas = repo.obtener_filas(limite=limite)
    return {
        "identificador": "comentarios_resumen_dataset",
        "filas": filas,
        "total_devuelto": len(filas),
    }
