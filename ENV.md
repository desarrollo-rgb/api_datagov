# Variables de entorno — API DataGov

Referencia de todas las variables del archivo `.env` para un despliegue **real** (no el
modo de desarrollo). Pensada para quien configura y despliega el servicio.

> **Reglas de oro**
> - El `.env` real **nunca** se sube a git. En producción (Cloud Run / GKE) estas variables
>   se cargan como variables de entorno de la plataforma, y los **secretos** desde
>   **Secret Manager**.
> - Los valores marcados como **🔒 Secreto** no deben quedar en texto plano en el repo ni
>   en logs.

---

## Seguridad

| Variable | Qué hace | Obligatoria | 🔒 | Valor real a usar |
| --- | --- | :---: | :---: | --- |
| `API_TOKEN` | Token que DataGov **exige** a quien lo consume (el DAG y la API ValleData). Se valida en la cabecera `Authorization: Bearer <token>`. | **Sí** (si falta, la app no arranca) | 🔒 | Un token largo y aleatorio. Generar con `openssl rand -hex 32`. Debe entregarse a los consumidores. |

---

## Flujo 1 — BigQuery (datos de cultivos)

| Variable | Qué hace | Obligatoria | 🔒 | Valor real a usar |
| --- | --- | :---: | :---: | --- |
| `USAR_DATOS_FALSOS` | Interruptor de modo. `true` = datos de ejemplo en memoria; `false` = consulta BigQuery real. | Sí | | `false` |
| `GCP_PROJECT_ID` | Proyecto de Google Cloud donde vive el dataset. | Sí | | `co-valledata-prd` |
| `BIGQUERY_DATASET` | Dataset de BigQuery que contiene la tabla. | Sí | | `valledata_qa` |
| `BIGQUERY_TABLA_CULTIVOS` | Nombre de la tabla de cultivos. | Sí | | `gold_cultivos_valle_geo` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Ruta al archivo `.json` de la service account. **Solo para local.** | No | 🔒 (el archivo) | **Vacío en producción**: la identidad la aporta la SA adjunta al servicio (Cloud Run / GKE). En local, la ruta al `.json`. |

**Permisos que necesita la service account** (rol IAM):
- `BigQuery Data Viewer` sobre el **dataset**.
- `BigQuery Job User` sobre el **proyecto** (sin este, no puede ejecutar consultas).

---

## Flujo 2 — cliente hacia la API ValleData (comentarios)

| Variable | Qué hace | Obligatoria | 🔒 | Valor real a usar |
| --- | --- | :---: | :---: | --- |
| `USAR_VALLEDATA_FALSO` | Interruptor de modo. `true` = comentarios de ejemplo; `false` = llama a ValleData por HTTP. | Sí | | `false` |
| `VALLEDATA_API_BASE_URL` | URL base de la API ValleData. | Sí | | URL del servicio ValleData desplegado (p. ej. `https://valledata....run.app`). En local: `http://localhost:8001`. |
| `VALLEDATA_API_TOKEN` | Token que DataGov **presenta** a ValleData al consumirla. | Sí | 🔒 | Debe ser **idéntico** al `API_TOKEN` configurado en ValleData. |
| `VALLEDATA_TIMEOUT_SEGUNDOS` | Segundos máximo de espera por respuesta de ValleData. | No (por defecto 30) | | `30` |

---

## Coincidencia de tokens entre servicios

DataGov participa en dos relaciones de autenticación. Estas igualdades **deben cumplirse**:

| Este valor… | …debe ser igual a… | Porque |
| --- | --- | --- |
| `DataGov.API_TOKEN` | `ValleData.DATAGOV_API_TOKEN` | ValleData consume el endpoint de cultivos de DataGov (Flujo 1). |
| `DataGov.VALLEDATA_API_TOKEN` | `ValleData.API_TOKEN` | DataGov consume el endpoint de comentarios de ValleData (Flujo 2). |

Si alguna no coincide, el consumidor recibe `401` y el endpoint que depende de ese llamado
responde `502`.

---

## Ejemplo de `.env` real (con secretos como marcadores)

```dotenv
# Seguridad
API_TOKEN=<secreto: openssl rand -hex 32>

# Flujo 1 — BigQuery
USAR_DATOS_FALSOS=false
GCP_PROJECT_ID=co-valledata-prd
BIGQUERY_DATASET=valledata_qa
BIGQUERY_TABLA_CULTIVOS=gold_cultivos_valle_geo
GOOGLE_APPLICATION_CREDENTIALS=

# Flujo 2 — cliente hacia ValleData
USAR_VALLEDATA_FALSO=false
VALLEDATA_API_BASE_URL=https://<host-de-valledata>
VALLEDATA_API_TOKEN=<secreto: igual al API_TOKEN de ValleData>
VALLEDATA_TIMEOUT_SEGUNDOS=30
```
