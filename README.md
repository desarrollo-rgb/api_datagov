# API DataGov

Capa de integración entre el proyecto **DataGov** (BigQuery) y el proyecto
**ValleData** (portales CKAN).

Documentos de referencia: [`CONTEXTO-API-DATAGOV.md`](CONTEXTO-API-DATAGOV.md) y
[`IMPLEMENTACION-API-DATAGOV.md`](IMPLEMENTACION-API-DATAGOV.md).

**Estado:** esqueleto inicial. Solo hay un endpoint de prueba.

- Python 3.11.9 (pyenv)
- FastAPI + Uvicorn

## Puesta en marcha

```bash
python -m venv .venv
```

```bash
.venv\Scripts\activate
```

```bash
pip install -r requirements-dev.txt
```

```bash
uvicorn app.main:app --reload --port 8000
```

- Endpoint: http://localhost:8000/
- Documentación interactiva: http://localhost:8000/docs

## Pruebas

```bash
pytest
```

## Estructura

```
app/
└── main.py     # aplicacion FastAPI
tests/
└── test_main.py
```
