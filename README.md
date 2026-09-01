# API DataGov

API en **FastAPI** que actúa como **capa de integración del proyecto DataGov** frente a
ValleData. Su primera responsabilidad es **exponer datos de BigQuery** (por ahora, una
tabla `agricultura`) a través de un endpoint protegido con token.

> Para entender **por qué** existe este servicio y cómo encaja en el ecosistema, lee los
> documentos de la carpeta [`documentacion/`](documentacion). Este README es para
> **instalar, correr y contribuir**; la parte conceptual está allí.

---

## ¿Qué hace hoy?

- `GET /` → un "hola mundo" público (sin token).
- `GET /health` y `GET /ready` → estado del servicio para la infraestructura. Públicos.
- `GET /api/v1/datasets/agricultura` → devuelve filas de agricultura. **Protegido por token.**

Actualmente corre en **modo de datos falsos**: responde con datos de ejemplo y **no toca
BigQuery**. Esto permite desarrollar sin credenciales reales. Cuando existan la service
account y la tabla reales, se cambia **una variable de entorno** y empieza a consultar
BigQuery de verdad (ver [Configuración](#4-configuración-el-archivo-env)).

---

## 1. Requisitos (se instalan una sola vez en tu máquina)

Necesitas dos herramientas antes de tocar el proyecto:

| Herramienta | Para qué sirve |
| --- | --- |
| **pyenv** | Instala y fija la versión de Python que usa el proyecto |
| **Poetry** | Gestiona las dependencias y el entorno virtual |

> Las instrucciones de abajo son para **Windows** (PowerShell), que es el entorno del
> equipo; al final hay una nota para Mac/Linux. **Tras instalar cada herramienta, cierra
> y vuelve a abrir la terminal** para que el PATH se actualice.

### 1.1 Instalar pyenv (pyenv-win)

1. Abre **PowerShell** y ejecuta el instalador oficial:

   ```powershell
   Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1" -OutFile "./install-pyenv-win.ps1"; &"./install-pyenv-win.ps1"
   ```

2. Cierra y vuelve a abrir PowerShell.
3. Comprueba que quedó instalado:

   ```powershell
   pyenv --version
   ```

   > Si dice que `pyenv` no se reconoce, reinicia el equipo (a veces el PATH solo toma
   > efecto tras reiniciar) o revisa la [guía de pyenv-win](https://github.com/pyenv-win/pyenv-win#installation).

### 1.2 Instalar Python con pyenv

pyenv no trae Python: lo instala. Instala la versión del proyecto y déjala como global
para que el comando `python` funcione en tu terminal:

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

1. Con Python ya disponible, instala Poetry con su instalador oficial:

   ```powershell
   (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
   ```

2. Al terminar, el instalador te muestra **la ruta que debes agregar al PATH**. En Windows
   suele ser:

   ```
   %APPDATA%\Python\Scripts
   ```

   Agrégala en *Configuración → Editar las variables de entorno del sistema → Path* y
   vuelve a abrir la terminal.
3. Comprueba:

   ```powershell
   poetry --version
   ```

> **Tip (opcional):** para que Poetry cree el entorno virtual dentro de cada proyecto en
> general, ejecuta `poetry config virtualenvs.in-project true`. Este repo ya lo trae
> configurado localmente (archivo `poetry.toml`), así que para *este* proyecto no hace falta.

> **Mac / Linux:** instala pyenv con su [guía oficial](https://github.com/pyenv/pyenv#installation)
> (o `brew install pyenv`) y Poetry con
> `curl -sSL https://install.python-poetry.org | python3 -`. Los demás pasos son iguales.

---

## 2. Puesta en marcha (clonar y correr)

Sigue estos pasos en orden. En total son ~5 minutos.

**1. Clona el repositorio y entra en la carpeta:**

```bash
git clone https://github.com/desarrollo-rgb/api_datagov.git
```

```bash
cd api_datagov
```

**2. Instala la versión de Python que el proyecto exige.**
El archivo `.python-version` ya fija `3.11.9`, así que solo tienes que instalarla:

```bash
pyenv install 3.11.9
```

**3. Crea tu archivo de configuración local** a partir de la plantilla:

```bash
cp .env.example .env
```

> El `.env` es tuyo y **no se sube a git**. Para desarrollar tal cual, no necesitas
> cambiar nada: viene listo en modo de datos falsos.

**4. Instala las dependencias** (Poetry creará el entorno `.venv/` dentro del proyecto):

```bash
poetry install
```

**5. Verifica que todo funciona corriendo las pruebas:**

```bash
poetry run pytest
```

Si ves algo como `6 passed`, ¡todo quedó bien!

**6. Levanta el servidor:**

```bash
poetry run uvicorn app.main:app --reload --port 8000
```

- Endpoint de prueba: http://localhost:8000/
- **Documentación interactiva:** http://localhost:8000/docs

`--reload` reinicia el servidor cada vez que guardas un archivo. Es solo para desarrollo.

---

## 3. Cómo está organizado el proyecto

```
api_datagov/
├── app/
│   ├── main.py                 # arranque de FastAPI; conecta los routers
│   ├── config.py               # lee el .env → objeto de configuración (Settings)
│   ├── security.py             # autenticación por token (el "guardián")
│   ├── api/
│   │   └── datasets.py         # endpoints que exponen datos (GET /agricultura)
│   └── services/
│       └── agricultura_repo.py # de dónde salen los datos: falso ↔ BigQuery
├── tests/                      # pruebas automatizadas
├── documentacion/              # contexto y arquitectura del proyecto
├── .env.example                # plantilla de configuración (SÍ se versiona)
├── .env                        # tu configuración local (NO se versiona)
├── .python-version             # versión de Python fijada (3.11.9)
├── pyproject.toml              # dependencias y configuración de herramientas
├── poetry.lock                 # versiones exactas: instalación reproducible
└── .gitignore
```

**La idea clave del diseño:** los endpoints (`api/`) no saben de dónde vienen los datos.
Eso lo decide `services/agricultura_repo.py` según la configuración. Así, pasar de datos
inventados a BigQuery real **no cambia ni una línea de la lógica**, solo la configuración.

---

## 4. Configuración: el archivo `.env`

Toda la configuración vive en variables de entorno (buena práctica: nada de valores fijos
ni secretos en el código). Estas son las variables:

| Variable | Qué es | Valor en desarrollo |
| --- | --- | --- |
| `API_TOKEN` | Token secreto que exige la API. **Obligatorio** (si falta, la app no arranca). | Un valor de prueba cualquiera |
| `USAR_DATOS_FALSOS` | `true` = datos de ejemplo, sin BigQuery. `false` = consulta BigQuery real. | `true` |
| `GCP_PROJECT_ID` | Proyecto de Google Cloud | `proyecto-dummy` |
| `BIGQUERY_DATASET` | Dataset donde vive la tabla | `agricultura_dataset` |
| `BIGQUERY_TABLA_AGRICULTURA` | Nombre de la tabla | `agricultura` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Ruta a la llave de la service account (solo local) | `./agricultura-sa.json` |

### Pasar a datos reales (cuando existan las credenciales y la tabla)

1. Consigue la llave de la service account (un `.json`) y colócala en la raíz del proyecto.
   > Nómbrala terminada en `-sa.json` (p. ej. `datagov-sa.json`): el `.gitignore` ya
   > ignora ese patrón, así que **no se subirá por error**.
2. En tu `.env`, ajusta:
   ```bash
   USAR_DATOS_FALSOS=false
   GCP_PROJECT_ID=tu-proyecto-real
   BIGQUERY_DATASET=el_dataset_real
   BIGQUERY_TABLA_AGRICULTURA=agricultura
   GOOGLE_APPLICATION_CREDENTIALS=./datagov-sa.json
   ```
3. Reinicia el servidor. No hay que tocar código.

> En producción (Cloud Run / GKE) `GOOGLE_APPLICATION_CREDENTIALS` se deja vacío: la
> identidad la aporta la service account "pegada" al servicio, sin archivos de llave.

---

## 5. Autenticación: cómo llamar a la API

Los endpoints de datos exigen un **token** en la cabecera `Authorization: Bearer <token>`.

Sin token → **401**:

```bash
curl -i "http://localhost:8000/api/v1/datasets/agricultura"
```

Con el token (el que tengas en tu `.env`, campo `API_TOKEN`) → **200 + datos**:

```bash
curl -i -H "Authorization: Bearer TU_TOKEN" "http://localhost:8000/api/v1/datasets/agricultura?limite=3"
```

Desde el navegador es más cómodo: entra a http://localhost:8000/docs, pulsa **Authorize**
🔒 (arriba a la derecha), pega el token una vez y ya puedes probar los endpoints.

---

## 6. Cómo contribuir / hacer cambios

**Flujo de trabajo recomendado:**

1. Crea una rama para tu cambio:
   ```bash
   git checkout -b feature/lo-que-vas-a-hacer
   ```
2. Haz tus cambios y **corre las pruebas** antes de subir:
   ```bash
   poetry run pytest
   ```
3. Haz commit y sube la rama; abre un Pull Request para revisión.

**Añadir una librería:**

```bash
poetry add nombre-libreria           # dependencia normal
poetry add --group dev nombre        # solo para desarrollo/pruebas
```

Esto actualiza `pyproject.toml` y `poetry.lock`. **Ambos se versionan**: así todos
instalan exactamente lo mismo.

**Convenciones del proyecto:**

- Código y comentarios **en español**, para acompañar el aprendizaje del equipo.
- **Nunca** subas secretos (tokens, llaves `.json`). Van en el `.env` o como llaves
  ignoradas por git. Si algo es secreto y debe conocerse, documéntalo en `.env.example`
  con un valor de ejemplo, no el real.
- Al consultar BigQuery: **nombres de tablas/columnas desde la configuración**, y los
  valores que llegan en la petición **siempre como parámetros** (nunca pegados al SQL).
  Es lo que evita la inyección SQL.
- Toda funcionalidad nueva debería venir con su prueba en `tests/`.

**Qué NO se sube al repo** (ya cubierto por `.gitignore`):

| No se sube | Por qué |
| --- | --- |
| `.env` | Contiene tu configuración local y secretos |
| `*-sa.json`, `key.json`, `credentials*.json` | Llaves de service accounts |
| `.venv/` | Se reconstruye con `poetry install` |
| `__pycache__/`, `.pytest_cache/` | Archivos temporales de Python |

---

## 7. Comandos del día a día

| Qué quieres hacer | Comando |
| --- | --- |
| Levantar el servidor | `poetry run uvicorn app.main:app --reload` |
| Correr las pruebas | `poetry run pytest` |
| Añadir una librería | `poetry add nombre` |
| Añadir una librería de desarrollo | `poetry add --group dev nombre` |
| Quitar una librería | `poetry remove nombre` |
| Ver las dependencias instaladas | `poetry show` |
| Abrir una consola dentro del entorno | `poetry env activate` |

---

## Documentos de referencia

En la carpeta [`documentacion/`](documentacion):

- [`CONTEXTO-API-DATAGOV.md`](documentacion/CONTEXTO-API-DATAGOV.md) — qué es este servicio y por qué existe.
- [`IMPLEMENTACION-API-DATAGOV.md`](documentacion/IMPLEMENTACION-API-DATAGOV.md) — notas de construcción por fases.
- [`CONTEXTO-API-VALLEDATA.md`](documentacion/CONTEXTO-API-VALLEDATA.md) y [`IMPLEMENTACION-API-VALLEDATA.md`](documentacion/IMPLEMENTACION-API-VALLEDATA.md) — el otro lado de la integración.
