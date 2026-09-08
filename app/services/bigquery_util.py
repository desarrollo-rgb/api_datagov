"""Utilidad compartida para consultar BigQuery de forma segura.

Centraliza la ejecucion de la consulta y la traduccion de errores. Si BigQuery falla
(tabla inexistente, permisos de la service account, conectividad), se lanza
`ErrorBigQueryNoDisponible`, que el manejador convierte en un 502 limpio (problema de
dependencia/config), en vez de un 500 (que reservamos para bugs del codigo).

La usan todos los repos de BigQuery, asi el manejo de errores es identico en todos.
"""

from app.errors import ErrorBigQueryNoDisponible


def ejecutar_consulta(client, consulta: str, job_config) -> list[dict]:
    """Ejecuta la consulta y devuelve las filas como diccionarios.

    `client` y `job_config` son de la libreria de BigQuery; se reciben ya construidos
    para no acoplar este helper (ni obligar a importar google) fuera del modo real.
    """
    try:
        resultado = client.query(consulta, job_config=job_config).result()
        return [dict(fila) for fila in resultado]
    except Exception as e:
        raise ErrorBigQueryNoDisponible(str(e)) from e
