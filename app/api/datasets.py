"""Endpoints que exponen las vistas de la analitica de comentarios (DataGov -> ValleData).

Las vistas viven en el dataset `gold_valledata`, por eso su URL usa ese nombre de dataset.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

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


def _parsear_fecha(valor: str | None) -> datetime | None:
    """Convierte una fecha ISO 8601 (fecha o fecha-hora) en datetime UTC sin zona.

    - Vacio o ausente -> None (no se filtra).
    - Acepta fecha (2026-10-10) o fecha y hora (2026-10-10T14:33:32, con o sin zona).
    - Formato invalido -> 422 (error de quien consume, no del servidor).
    """
    if valor is None or valor.strip() == "":
        return None
    try:
        dt = datetime.fromisoformat(valor)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Parametro 'fecha_hora_publicacion' invalido. Usa ISO 8601, por ejemplo 2026-10-10 o 2026-10-10T14:33:32.",
        )
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


@router.get(
    "/valledata_api_comentarios_detalle",
    summary="Obtener el detalle de comentarios analizados",
)
async def obtener_comentarios_detalle(
    limite: int | None = _LIMITE,
    fecha_hora_publicacion: str | None = Query(
        default=None,
        description=(
            "Trae los comentarios publicados DESDE esta fecha/hora en adelante "
            "(fecha_hora_publicacion >= valor). Acepta ISO 8601: fecha (2026-10-10) o "
            "fecha y hora (2026-10-10T14:33:32). Vacio = todos."
        ),
    ),
    municipio: str | None = Query(
        default=None,
        description="Filtra por municipio. No distingue mayusculas/minusculas (se compara en MAYUSCULA).",
    ),
    repo: ComentariosDetalleRepo = Depends(get_comentarios_detalle_repo),
) -> dict:
    """Devuelve el detalle de comentarios ya analizados (un comentario por fila, con su sentimiento y emoción) de la vista valledata_api_comentarios_detalle en BigQuery. Se puede filtrar por `fecha_hora_publicacion` (desde) y por `municipio`."""
    fecha = _parsear_fecha(fecha_hora_publicacion)
    muni = municipio.strip().upper() if municipio and municipio.strip() else None
    filas = repo.obtener_filas(limite=limite, fecha_hora_publicacion=fecha, municipio=muni)
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
