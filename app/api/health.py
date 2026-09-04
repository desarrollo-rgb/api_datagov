"""Endpoints de salud para la infraestructura (Cloud Run / GKE / balanceador).

No los consume ValleData ni un humano: los llama la plataforma para saber si la app
esta viva y si puede recibir trafico. Por eso son PUBLICOS (sin token) y no exponen
datos sensibles.

- /health (liveness): "¿el proceso responde?" -> si falla repetidamente, la plataforma
  REINICIA el contenedor.
- /ready  (readiness): "¿puede trabajar de verdad?" (sus dependencias responden) -> si
  falla, la plataforma DEJA DE ENVIARLE TRAFICO hasta que se recupere, sin reiniciarlo.
"""

import logging

from fastapi import APIRouter, HTTPException, status

from app.config import get_settings

logger = logging.getLogger("datagov")

router = APIRouter(tags=["salud"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness: responde mientras el proceso este vivo. No revisa dependencias.

    Es importante que NO consulte BigQuery: si lo hiciera, un problema de BigQuery
    provocaria reinicios innecesarios del contenedor.
    """
    return {"status": "alive"}


@router.get("/ready")
async def ready() -> dict[str, str]:
    """Readiness: confirma que la app puede atender (sus dependencias responden)."""
    listo, detalle = _dependencias_listas()
    if not listo:
        # 503: estoy vivo, pero todavia no puedo atender. La plataforma no me enviara
        # trafico hasta que /ready vuelva a responder 200.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not ready", "detail": detalle},
        )
    return {"status": "ready", "detail": detalle}


def _dependencias_listas() -> tuple[bool, str]:
    """Comprueba las dependencias necesarias para trabajar.

    - En modo datos falsos no hay dependencias externas: siempre listo.
    - En modo real hace una comprobacion barata (dry run) de que BigQuery responde.
    """
    settings = get_settings()

    if settings.usar_datos_falsos:
        return True, "fake data mode"

    try:
        import os

        from google.cloud import bigquery

        if settings.google_application_credentials:
            os.environ.setdefault(
                "GOOGLE_APPLICATION_CREDENTIALS",
                settings.google_application_credentials,
            )

        cliente = bigquery.Client(project=settings.gcp_project_id)
        # dry_run NO ejecuta la consulta: solo valida credenciales y conectividad.
        # Es barato y no genera costo de BigQuery.
        configuracion = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
        cliente.query("SELECT 1", job_config=configuracion)
        return True, "bigquery reachable"
    except Exception as e:
        # Al consumidor no le exponemos el detalle, pero SI lo registramos en el log.
        logger.warning("Readiness: BigQuery no responde: %s", e)
        return False, "bigquery unavailable"
