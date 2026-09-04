# Manejo de errores — API DataGov

Guía para diagnosticar fallos: **qué responde** la API ante cada error y **qué se registra
en el log**, para distinguir rápido si el problema es del que consume (mal uso), de una
dependencia externa, o del código.

---

## ¿Dónde veo por qué falló?

La API escribe cada error en la **consola (`stdout`)**. Según dónde corra:

- **Local:** en la terminal donde tienes `uvicorn`.
- **Producción (Cloud Run / GKE):** GCP lo captura automáticamente en **Cloud Logging**.

Consultar en producción:

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=datagov" --limit 50
```

O desde la consola de GCP: **Logging → Logs Explorer**, filtrando por el servicio.

---

## Cómo leer el código de estado

| Código | De quién es el problema |
| --- | --- |
| **4xx** 🟡 | Del que llama: token, parámetros o ruta. **No es el código de la API.** |
| **502 / 503** 🔵 | Una dependencia externa (ValleData, BigQuery) o la infraestructura. |
| **500** 🔴 | El código o la configuración. El log trae el **stack trace completo**. |

Además, uvicorn escribe una línea por cada petición con su código, por ejemplo:

```
INFO:  10.0.0.5 - "GET /api/v1/bd_ckan/comments HTTP/1.1" 502
```

---

## Tabla de fallos

| # | Escenario | HTTP | Cuerpo (`detail`) | Qué verás en el log | Categoría |
|---|---|---|---|---|---|
| 1 | Llamada sin token | **401** | `"No autorizado"` | Línea de acceso `... 401` | 🟡 Mal consumo |
| 2 | Token equivocado | **401** | `"No autorizado"` | Línea de acceso `... 401` | 🟡 Mal consumo |
| 3 | `?limite=0` (o > 1000) en cultivos | **422** | detalle de validación | Línea de acceso `... 422` | 🟡 Mal consumo |
| 4 | Ruta que no existe | **404** | `"Not Found"` | Línea de acceso `... 404` | 🟡 Mal consumo |
| 5 | ValleData caído (al pedir comentarios) | **502** | `"No se pudo contactar a la API ValleData. Intenta más tarde."` | `WARNING: ValleData no disponible: [Errno 111] Connection refused` | 🔵 Dependencia |
| 6 | ValleData responde con error (p. ej. 500) | **502** | `"La API ValleData respondió con un error."` | `WARNING: ValleData respondio con error: codigo 500` | 🔵 Dependencia |
| 7 | `VALLEDATA_API_TOKEN` no coincide con el de ValleData | **502** | `"La API ValleData respondió con un error."` | `WARNING: ValleData respondio con error: codigo 401` | 🟡 Mala config |
| 8 | Un municipio falló en ValleData | **200** | `municipios_con_error: ["ulloa"]` | (el detalle se registra en ValleData, no aquí) | 🔵 Dependencia |
| 9 | `/ready` con BigQuery caído o sin credenciales | **503** | `"not ready"` | `WARNING: Readiness: BigQuery no responde: ...` | 🔵 Infra |
| 10 | BigQuery sin permisos / tabla no existe (al pedir cultivos) | **500** | `"Error interno del servidor."` | `ERROR` + **stack trace completo** | 🔴 Revisar config/código |
| 11 | Excepción no prevista (bug real) | **500** | `"Error interno del servidor."` | `ERROR` + **stack trace completo** | 🔴 Bug de código |

---

## Principios de diseño

- **Al consumidor nunca se le expone el detalle técnico:** los mensajes son genéricos. El
  detalle (motivo, stack trace) va solo al log.
- **Un fallo de una dependencia no se disfraza de éxito:** si ValleData falla, respondemos
  `502`, no un `200` vacío.
- **Fallos parciales de datos se informan, no se ocultan:** `municipios_con_error` indica
  qué municipios no vinieron, para que el DAG sepa si la ingesta está incompleta.

> Nota: hoy los errores de BigQuery en el endpoint de cultivos caen en el `500` genérico
> (esa consulta no está envuelta como el cliente de ValleData). Queda registrado completo
> en el log. Un ajuste futuro sería envolverlos para responder `502`/`503` (dependencia) en
> vez de `500`.
