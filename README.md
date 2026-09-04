# API DataGov

API en **FastAPI** que actúa como **capa de integración del proyecto DataGov** frente a
ValleData. Tiene dos responsabilidades:

1. **Exponer datos de cultivos** desde BigQuery (tabla `gold_cultivos_valle_geo`).
2. **Consumir los comentarios** que expone ValleData (que a su vez los lee de los portales
   CKAN) y **reexponerlos** para que un DAG de analítica los ingiera.

Este README cubre cómo **instalar, configurar, correr y contribuir**.

---

## ¿Qué expone? (endpoints)

| Método y ruta | Qué devuelve | Token |
| --- | --- | --- |
| `GET /health` | Liveness: `{"status": "alive"}`. Para la plataforma. | No |
| `GET /ready` | Readiness: revisa que BigQuery responda. `200` o `503`. | No |
| `GET /api/v1/dataset_valledata/gold_cultivos_valle_geo` | Filas de cultivos desde BigQuery (Flujo 1). Parámetro `limite` (1–1000). | **Sí** |
| `GET /api/v1/bd_ckan/comments` | Comentarios que DataGov obtuvo de ValleData, con `municipios_con_error` (Flujo 2). | **Sí** |

**Documentación interactiva** (Swagger) cuando el servidor está arriba: http://localhost:8000/docs

---

## Los dos modos: falso y real

Cada dependencia externa (BigQuery y ValleData) tiene **dos implementaciones** detrás de la
misma interfaz, y se elige por configuración:

- **Modo falso** (`true`): responde con datos de ejemplo en memoria. **No toca BigQuery ni
  llama a ValleData.** Ideal para desarrollar y correr las pruebas sin credenciales ni red.
- **Modo real** (`false`): consulta BigQuery / llama a ValleData de verdad.

Se controla con `USAR_DATOS_FALSOS` (BigQuery) y `USAR_VALLEDATA_FALSO` (ValleData). Pasar
de falso a real **no cambia ni una línea de código**, solo el `.env`.

---

## 1. Requisitos (se instalan una sola vez en tu máquina)

| Herramienta | Para qué sirve |
| --- | --- |
| **pyenv** | Instala y fija la versión de Python que usa el proyecto (3.11.9) |
| **Poetry** | Gestiona las dependencias y el entorno virtual |

> Instrucciones para **Windows** (PowerShell), que es el entorno del equipo; al final hay
> una nota para Mac/Linux. **Tras instalar cada herramienta, cierra y vuelve a abrir la
> terminal** para que el PATH se actualice.

### 1.1 Instalar pyenv (pyenv-win)

1. Abre **PowerShell** y ejecuta el instalador oficial:

   ```powershell
   Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1" -OutFile "./install-pyenv-win.ps1"; &"./install-pyenv-win.ps1"
   ```

2. Cierra y vuelve a abrir PowerShell.
3. Comprueba: `pyenv --version`

   > Si dice que `pyenv` no se reconoce, reinicia el equipo (a veces el PATH solo toma
   > efecto tras reiniciar) o revisa la [guía de pyenv-win](https://github.com/pyenv-win/pyenv-win#installation).

### 1.2 Instalar Python con pyenv

```powershell
pyenv install 3.11.9
```
```powershell
pyenv global 3.11.9
```
```powershell
python --version
```

Debe imprimir `Python 3.11.9`.

### 1.3 Instalar Poetry

1. Instala Poetry con su instalador oficial:

   ```powershell
   (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
   ```

2. Al terminar, el instalador te muestra **la ruta que debes agregar al PATH**. En Windows
   suele ser `%APPDATA%\Python\Scripts`. Agrégala en *Configuración → Editar las variables
   de entorno del sistema → Path* y vuelve a abrir la terminal.
3. Comprueba: `poetry --version`

> Este repo ya trae `poetry.toml` para crear el entorno virtual dentro del proyecto
> (`.venv/`), así que no necesitas configurar nada extra.

> **Mac / Linux:** pyenv con su [guía oficial](https://github.com/pyenv/pyenv#installation)
> (o `brew install pyenv`) y Poetry con `curl -sSL https://install.python-poetry.org | python3 -`.

---

## 2. Puesta en marcha (clonar y correr en modo falso)

Con esto tienes la API corriendo **sin credenciales** en ~5 minutos.

**1. Clona el repositorio y entra en la carpeta:**

```bash
git clone https://github.com/desarrollo-rgb/api_datagov.git
```
```bash
cd api_datagov
```

**2. Instala la versión de Python que el proyecto exige** (`.python-version` ya fija `3.11.9`):

```bash
pyenv install 3.11.9
```

**3. Crea tu archivo de configuración local** a partir de la plantilla:

```bash
cp .env.example .env
```

**4. Pon un token cualquiera en el `.env`.** `API_TOKEN` es **obligatorio**: si falta, la
app no arranca. Para desarrollo sirve cualquier valor, por ejemplo:

```
API_TOKEN=dev-local-token-de-prueba
```

> El `.env` es tuyo y **no se sube a git**. En modo falso no necesitas nada más.

**5. Instala las dependencias** (Poetry crea el entorno `.venv/` dentro del proyecto):

```bash
poetry install
```

**6. Verifica que todo funciona corriendo las pruebas:**

```bash
poetry run pytest
```

Si ves `13 passed`, todo quedó bien. (Las pruebas corren siempre en modo falso, sin tocar
BigQuery ni ValleData, gracias a `tests/conftest.py`.)

**7. Levanta el servidor:**

```bash
poetry run uvicorn app.main:app --reload --port 8000
```

- Documentación interactiva: http://localhost:8000/docs
- Health check: http://localhost:8000/health

`--reload` reinicia el servidor cada vez que guardas un archivo. Es solo para desarrollo.

---

## 3. Configuración: el archivo `.env`

Toda la configuración vive en variables de entorno (nada de valores fijos ni secretos en
el código).

### Seguridad

| Variable | Qué es | Valor en desarrollo |
| --- | --- | --- |
| `API_TOKEN` | Token que exige ESTA API. **Obligatorio** (si falta, no arranca). | Un valor de prueba |

### Flujo 1 — BigQuery (cultivos)

| Variable | Qué es | Desarrollo (falso) |
| --- | --- | --- |
| `USAR_DATOS_FALSOS` | `true` = datos de ejemplo; `false` = BigQuery real | `true` |
| `GCP_PROJECT_ID` | Proyecto de Google Cloud | `proyecto-dummy` |
| `BIGQUERY_DATASET` | Dataset donde vive la tabla | `agricultura_dataset` |
| `BIGQUERY_TABLA_CULTIVOS` | Nombre de la tabla | `gold_cultivos_valle_geo` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Ruta a la llave de la service account (solo local) | `./agricultura-sa.json` |

### Flujo 2 — cliente hacia ValleData (comentarios)

| Variable | Qué es | Desarrollo (falso) |
| --- | --- | --- |
| `USAR_VALLEDATA_FALSO` | `true` = comentarios de ejemplo; `false` = llama a ValleData | `true` |
| `VALLEDATA_API_BASE_URL` | URL base de la API ValleData | `http://localhost:8001` |
| `VALLEDATA_API_TOKEN` | Token que ValleData exige. **Debe ser idéntico al `API_TOKEN` de ValleData.** | — |
| `VALLEDATA_TIMEOUT_SEGUNDOS` | Timeout de las llamadas | `30` |

---

## 4. Pasar a datos reales

### 4.1 BigQuery (Flujo 1)

1. Consigue la llave de la service account (`.json`) y colócala en la raíz del proyecto.
   > Nómbrala terminada en `-sa.json` (p. ej. `datagov-sa.json`): el `.gitignore` ya
   > ignora ese patrón, así que **no se subirá por error**.
2. En tu `.env`:
   ```
   USAR_DATOS_FALSOS=false
   GCP_PROJECT_ID=co-valledata-prd
   BIGQUERY_DATASET=valledata_qa
   BIGQUERY_TABLA_CULTIVOS=gold_cultivos_valle_geo
   GOOGLE_APPLICATION_CREDENTIALS=C:\ruta\a\tu-sa.json
   ```
3. La service account necesita **dos** permisos: `BigQuery Data Viewer` (sobre el dataset) y
   `BigQuery Job User` (sobre el proyecto). Sin el segundo, no puede ejecutar consultas.
4. Reinicia el servidor. No hay que tocar código.

> En producción (Cloud Run / GKE) `GOOGLE_APPLICATION_CREDENTIALS` se deja **vacío**: la
> identidad la aporta la service account "pegada" al servicio, sin archivos de llave.

### 4.2 ValleData (Flujo 2)

1. Ten la API ValleData corriendo (por defecto en `http://localhost:8001`).
2. En tu `.env`:
   ```
   USAR_VALLEDATA_FALSO=false
   VALLEDATA_API_BASE_URL=http://localhost:8001
   VALLEDATA_API_TOKEN=<el mismo API_TOKEN configurado en ValleData>
   ```
   > 🔑 Si `VALLEDATA_API_TOKEN` no coincide con el `API_TOKEN` de ValleData, DataGov
   > recibirá `401` y este endpoint responderá `502`.
3. Reinicia el servidor.

---

## 5. Autenticación: cómo llamar a la API

Los endpoints de datos exigen un **token** en la cabecera `Authorization: Bearer <token>`
(el valor de tu `API_TOKEN`).

Sin token → **401**:

```bash
curl -i "http://localhost:8000/api/v1/dataset_valledata/gold_cultivos_valle_geo"
```

Con el token → **200 + datos**:

```bash
curl -i -H "Authorization: Bearer TU_TOKEN" "http://localhost:8000/api/v1/dataset_valledata/gold_cultivos_valle_geo?limite=3"
```

Desde el navegador: entra a http://localhost:8000/docs, pulsa **Authorize** 🔒 (arriba a la
derecha), pega el token una vez y prueba los endpoints.

---

## 6. Cómo está organizado el proyecto

```
api_datagov/
├── app/
│   ├── main.py                 # arranque de FastAPI; conecta routers y manejadores de error
│   ├── config.py               # lee el .env → objeto de configuración (Settings)
│   ├── security.py             # autenticación por token (el "guardián")
│   ├── errors.py               # excepciones de dominio + respuestas de error limpias
│   ├── models/
│   │   └── schemas.py          # contrato de datos (Comentario)
│   ├── api/
│   │   ├── health.py           # GET /health y GET /ready (públicos)
│   │   ├── datasets.py         # GET .../gold_cultivos_valle_geo (BigQuery)
│   │   └── comentarios.py      # GET .../comments (reexpone ValleData)
│   └── services/
│       ├── agricultura_repo.py # de dónde salen los cultivos: falso ↔ BigQuery
│       └── valledata_client.py # cómo se piden los comentarios: falso ↔ HTTP a ValleData
├── tests/                      # pruebas (conftest.py fuerza modo falso)
├── .env.example                # plantilla de configuración (SÍ se versiona)
├── .env                        # tu configuración local (NO se versiona)
├── .python-version             # versión de Python fijada (3.11.9)
├── pyproject.toml / poetry.lock
└── .gitignore
```

**La idea clave del diseño:** los endpoints (`api/`) no saben de dónde vienen los datos.
Eso lo deciden los `services/` según la configuración. Por eso pasar de datos inventados a
reales es solo cambiar el `.env`.

---

## 7. Manejo de errores

- Si **ValleData está caído** o responde con error, el endpoint de comentarios devuelve un
  **502** limpio (`"No se pudo contactar a la API ValleData"`), no un 500 con traza.
- Cualquier error no previsto devuelve un **500** genérico; el detalle técnico va al log,
  nunca a la respuesta.
- `GET /ready` devuelve **503** si BigQuery no responde (en modo real).

---

## 8. Cómo contribuir / hacer cambios

1. Crea una rama: `git checkout -b feature/lo-que-vas-a-hacer`
2. Haz tus cambios y **corre las pruebas** antes de subir: `poetry run pytest`
3. Commit, sube la rama y abre un Pull Request.

**Añadir una librería:**

```bash
poetry add nombre-libreria           # dependencia normal
poetry add --group dev nombre        # solo para desarrollo/pruebas
```

**Convenciones del proyecto:**

- Código y comentarios **en español**.
- **Nunca** subas secretos (tokens, llaves `.json`). Van en el `.env` o como llaves
  ignoradas por git. Si algo es secreto y debe conocerse, documéntalo en `.env.example`
  con un valor de ejemplo.
- Al consultar BigQuery: **nombres de tablas/columnas desde la configuración**, y los
  valores de la petición **siempre como parámetros** (nunca pegados al SQL). Evita inyección.
- Toda funcionalidad nueva debería venir con su prueba en `tests/`.

**Qué NO se sube al repo** (ya cubierto por `.gitignore`):

| No se sube | Por qué |
| --- | --- |
| `.env` | Configuración local y secretos |
| `*-sa.json`, `key.json`, `credentials*.json` | Llaves de service accounts |
| `.venv/` | Se reconstruye con `poetry install` |
| `__pycache__/`, `.pytest_cache/` | Temporales de Python |

---

## 9. Comandos del día a día

| Qué quieres hacer | Comando |
| --- | --- |
| Levantar el servidor | `poetry run uvicorn app.main:app --reload --port 8000` |
| Correr las pruebas | `poetry run pytest` |
| Añadir una librería | `poetry add nombre` |
| Añadir una librería de desarrollo | `poetry add --group dev nombre` |
| Quitar una librería | `poetry remove nombre` |
| Ver las dependencias instaladas | `poetry show` |
| Abrir una consola dentro del entorno | `poetry env activate` |
