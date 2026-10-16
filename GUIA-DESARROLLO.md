# Guía de desarrollo — API DataGov (para empezar desde cero)

Esta guía es para alguien que **nunca ha tocado el repo**. Explica cómo clonarlo, correrlo
y cómo **agregar un endpoint nuevo** paso a paso. No asume experiencia previa con el
proyecto.

> ¿Qué hace esta API? Expone en HTTP las **vistas de la analítica de comentarios** que
> viven en BigQuery (dataset `gold_valledata`) y reexpone los comentarios crudos que lee de
> la API ValleData. Si no lo tienes claro, lee primero el `README.md`.

---

## 1. Requisitos (se instalan una sola vez)


| Herramienta | Para qué                                        | Cómo comprobar     |
| ----------- | ----------------------------------------------- | ------------------ |
| **pyenv**   | Fija la versión de Python del proyecto (3.11.9) | `pyenv --version`  |
| **Poetry**  | Instala dependencias y crea el entorno virtual  | `poetry --version` |
| **git**     | Clonar el repo                                  | `git --version`    |


> Instalación en Windows (PowerShell): pyenv-win y Poetry tienen instaladores oficiales.
> Tras instalar cada uno, **cierra y abre la terminal** para que el PATH se actualice.

---



## 2. Clonar y dejar el proyecto corriendo

```bash
# 1) Clonar el repo
git clone https://github.com/desarrollo-rgb/api_datagov.git
cd api_datagov

# 2) Usar la version de Python del proyecto (la fija el archivo .python-version)
pyenv install 3.11.9   # solo si no la tienes
pyenv local 3.11.9

# 3) Instalar dependencias (crea el entorno virtual)
poetry install

# 4) Crear tu archivo de configuracion a partir de la plantilla
cp .env.example .env
# Abre .env y pon al menos:  API_TOKEN=cualquier-cosa   y   USAR_DATOS_FALSOS=true
# Con USAR_DATOS_FALSOS=true arranca con datos de ejemplo, sin credenciales de BigQuery.

# 5) Levantar el servidor
poetry run uvicorn app.main:app --reload --port 8000
```

Abre **[http://localhost:8000/docs](http://localhost:8000/docs)** → es Swagger, la interfaz para probar los endpoints.
Dale a **Authorize** 🔒, pega tu `API_TOKEN`, y ya puedes ejecutar los endpoints.

Para correr las pruebas:

```bash
poetry run pytest
```

---



## 3. Cómo está organizado (lo mínimo que debes saber)

```
app/
├── main.py            # arranca FastAPI y "enchufa" los routers
├── config.py          # TODAS las variables de entorno (clase Settings)
├── security.py        # el guardian: valida el token (no lo tocas casi nunca)
├── errors.py          # traduce errores a respuestas HTTP limpias (502, 500, ...)
├── api/
│   ├── datasets.py    # endpoints que exponen las vistas de BigQuery  <-- aqui agregas
│   └── comentarios.py # endpoint que reexpone los comentarios de ValleData
└── services/
    ├── comentarios_detalle_repo.py   # "de donde salen los datos": Falso <-> BigQuery
    ├── comentarios_resumen_repo.py
    ├── bigquery_util.py              # helper que ejecuta la consulta en BigQuery
    └── valledata_client.py           # cliente HTTP hacia ValleData
```

**La idea clave (patrón que se repite):** cada endpoint tiene un **repositorio** con
*una interfaz y dos implementaciones*:

- una **Falsa** (datos de ejemplo en memoria, para desarrollar sin BigQuery), y
- una **real** (consulta BigQuery).

El endpoint no sabe cuál se usa; lo decide una variable de entorno (`USAR_DATOS_FALSOS`).
Por eso puedes desarrollar y probar sin credenciales.

---



## 4. Agregar un endpoint nuevo (exponer una vista/tabla de BigQuery)

Supongamos que quieres exponer una vista nueva de BigQuery llamada `mi_vista_nueva`.
Son **4 pasos**. Lo más fácil es **copiar** un archivo que ya existe y cambiarle los nombres.

### Paso 1 — Declarar la vista en la configuración

En `app/config.py`, dentro de la clase `Settings`, agrega el nombre de la vista (y el
dataset si es otro):

```python
# en app/config.py
bigquery_vista_mi_vista_nueva: str = "mi_vista_nueva"
```

Y súmala a `.env` y a `.env.example` (con un comentario corto, como las demás):

```dotenv
# Vista nueva de ejemplo.
BIGQUERY_VISTA_MI_VISTA_NUEVA=mi_vista_nueva
```



### Paso 2 — Crear el repositorio (de dónde salen los datos)

Copia `app/services/comentarios_resumen_repo.py` a
`app/services/mi_vista_nueva_repo.py` y cambia:

- el nombre de las clases (`...Repo`, `...RepoFalso`, `...RepoBigQuery`),
- los datos de ejemplo de `_FILAS_EJEMPLO`,
- la vista que consulta (`s.bigquery_vista_mi_vista_nueva`),
- la función `get_..._repo()` del final.

Lo esencial que no cambia es la forma de la consulta (está en `...RepoBigQuery.obtener_filas`):

```python
tabla = f"`{s.gcp_project_id}.{s.bigquery_dataset_comentarios}.{s.bigquery_vista_mi_vista_nueva}`"
# SELECT * con limite parametrizado; usa el helper ejecutar_consulta(...)
```

> **Nunca** metas valores del usuario directo en el SQL: van como parámetros
> (`@limite`, `@municipio`, ...). Eso evita inyección SQL.



### Paso 3 — Crear el endpoint

En `app/api/datasets.py`, agrega una función con el mismo patrón que las existentes:

```python
from app.services.mi_vista_nueva_repo import MiVistaNuevaRepo, get_mi_vista_nueva_repo

@router.get(
    "/mi_vista_nueva",
    summary="Obtener los datos de mi vista nueva",
)
async def obtener_mi_vista_nueva(
    limite: int | None = _LIMITE,
    repo: MiVistaNuevaRepo = Depends(get_mi_vista_nueva_repo),
) -> dict:
    """Describe aqui que devuelve el endpoint."""
    filas = repo.obtener_filas(limite=limite)
    return {
        "identificador": "mi_vista_nueva",
        "filas": filas,
        "total_devuelto": len(filas),
    }
```

- El `router` ya existe con el prefijo `/api/v1/expose/gold_valledata` y ya exige token,
así que tu endpoint quedará en
`GET /api/v1/expose/gold_valledata/mi_vista_nueva`.
- `_LIMITE` (el parámetro opcional `limite`) ya está definido arriba en el archivo.

> ¿Necesitas filtros (como `municipio` o una fecha)? Mira el endpoint
> `valledata_api_comentarios_detalle` en ese mismo archivo: recibe parámetros extra, los
> valida y se los pasa al repo, que los convierte en `WHERE ... = @param` parametrizados.



### Paso 4 — Agregar una prueba

Copia `tests/test_comentarios_resumen.py` a `tests/test_mi_vista_nueva.py`, cambia la
`RUTA` y las columnas esperadas, y corre:

```bash
poetry run pytest
```

Verifica también en Swagger (`/docs`) que el endpoint responde.

---



## 5. Caso especial: un router con otro prefijo de URL

Si tu endpoint **no** va bajo `/gold_valledata` (por ejemplo, otra fuente de datos), se crea
un `APIRouter` nuevo con su propio `prefix` en `datasets.py` (o en un archivo nuevo dentro
de `app/api/`) y se **registra en** `app/main.py` con `app.include_router(...)`. Guíate por
cómo está hecho `comentarios.py` (que usa el prefijo `/api/v1/consume/bd_ckan`).

---



## 6. Checklist para tu Pull Request

- [ ] Variable(s) en `config.py`, `.env` y `.env.example`.
- [ ] Repositorio en `services/` (Falso + real).
- [ ] Endpoint en `api/` (con token y descripción clara).
- [ ] Router nuevo registrado en `main.py` (solo si creaste uno).
- [ ] Prueba en `tests/` y `poetry run pytest` en verde.
- [ ] Probado en Swagger con modo falso.
- [ ] Si tocaste variables de entorno, avisaste para que se ajuste el despliegue.