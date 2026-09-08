"""Endpoints que exponen datos de la capa Gold (Parte 1: DataGov -> ValleData)."""

from fastapi import APIRouter, Depends, Query

from app.config import get_settings
from app.security import verificar_token
from app.services.agricultura_repo import AgriculturaRepo, get_agricultura_repo
from app.services.pronostico_repo import PronosticoRepo, get_pronostico_repo
from app.services.rendimiento_repo import RendimientoRepo, get_rendimiento_repo
from app.services.sentimiento_repo import SentimientoRepo, get_sentimiento_repo

# La dependencia va en el router: protege TODOS los endpoints de datasets de una vez.
router = APIRouter(
    prefix="/api/v1/expose/dataset_valledata",
    tags=["dataset Valledata"],
    dependencies=[Depends(verificar_token)],
)

# Rango del parametro `limite`, leido de la configuracion (variables LIMITE_MINIMO y
# LIMITE_MAXIMO). Se resuelve al arrancar: cambiarlo en el .env solo requiere reiniciar.
_s = get_settings()
_LIMITE = Query(
    default=None,
    ge=_s.limite_minimo_select,
    le=_s.limite_maximo_select,
    description="Maximo de filas a devolver. Vacio = todas (o el maximo, segun PERMITIR_FULL_SELECT).",
)


def _resolver_limite(limite: int | None) -> int | None:
    """Aplica la politica de 'full select' cuando no se especifica `limite`.

    - PERMITIR_FULL_SELECT=true  -> None (se devuelven todas las filas).
    - PERMITIR_FULL_SELECT=false -> se topa en LIMITE_MAXIMO_SELECT.
    Si se especifica un `limite`, se respeta tal cual (ya validado por el rango).
    """
    s = get_settings()
    if limite is None and not s.permitir_full_select:
        return s.limite_maximo_select
    return limite


@router.get(
    "/gold_cultivos_valle_geo",
    summary="Obtener información de la tabla de cultivos",
)
async def obtener_agricultura(
    limite: int | None = _LIMITE,
    repo: AgriculturaRepo = Depends(get_agricultura_repo),
) -> dict:
    """Devuelve los datos de cultivos de la tabla gold_cultivos_valle_geo en BigQuery."""
    # El endpoint no sabe si los datos vienen de BigQuery o de ejemplos: eso lo resuelve
    # get_agricultura_repo() segun la configuracion.
    filas = repo.obtener_filas(limite=_resolver_limite(limite))
    return {
        "identificador": "agricultura",
        "filas": filas,
        "total_devuelto": len(filas),
    }


@router.get(
    "/gold_modelo_rendimiento",
    summary="Obtener información de la tabla de rendimiento",
)
async def obtener_rendimiento(
    limite: int | None = _LIMITE,
    repo: RendimientoRepo = Depends(get_rendimiento_repo),
) -> dict:
    """Devuelve los datos del modelo de rendimiento de la tabla gold_modelo_rendimiento en BigQuery."""
    filas = repo.obtener_filas(limite=_resolver_limite(limite))
    return {
        "identificador": "rendimiento",
        "filas": filas,
        "total_devuelto": len(filas),
    }


@router.get(
    "/gold_pronostico_produccion",
    summary="Obtener información de la tabla de pronóstico de producción",
)
async def obtener_pronostico(
    limite: int | None = _LIMITE,
    repo: PronosticoRepo = Depends(get_pronostico_repo),
) -> dict:
    """Devuelve los datos del pronóstico de producción de la tabla gold_pronostico_produccion en BigQuery."""
    filas = repo.obtener_filas(limite=_resolver_limite(limite))
    return {
        "identificador": "pronostico",
        "filas": filas,
        "total_devuelto": len(filas),
    }


@router.get(
    "/gold_comentarios_sentimiento",
    summary="Obtener información de la tabla de sentimiento de comentarios",
)
async def obtener_sentimiento(
    limite: int | None = _LIMITE,
    repo: SentimientoRepo = Depends(get_sentimiento_repo),
) -> dict:
    """Devuelve el análisis de sentimiento de comentarios de la tabla gold_comentarios_sentimiento en BigQuery."""
    filas = repo.obtener_filas(limite=_resolver_limite(limite))
    return {
        "identificador": "sentimiento",
        "filas": filas,
        "total_devuelto": len(filas),
    }
