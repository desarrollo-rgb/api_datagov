from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app

cliente = TestClient(app)

# Cabecera con el token correcto, tomado de la configuracion (asi la prueba no depende
# de un valor escrito a mano: usa el mismo token que la app).
CABECERA_VALIDA = {"Authorization": f"Bearer {get_settings().api_token}"}


def test_agricultura_devuelve_datos_falsos():
    respuesta = cliente.get("/api/v1/datasets/agricultura?limite=2", headers=CABECERA_VALIDA)
    assert respuesta.status_code == 200

    cuerpo = respuesta.json()
    assert cuerpo["identificador"] == "agricultura"
    assert cuerpo["total_devuelto"] == 2
    assert len(cuerpo["filas"]) == 2
    assert set(cuerpo["filas"][0]) == {
        "municipio",
        "cultivo",
        "area_hectareas",
        "produccion_toneladas",
        "anio",
    }


def test_agricultura_respeta_el_limite():
    respuesta = cliente.get("/api/v1/datasets/agricultura?limite=1000", headers=CABECERA_VALIDA)
    assert respuesta.status_code == 200
    assert respuesta.json()["total_devuelto"] == 5


def test_agricultura_rechaza_limite_invalido():
    respuesta = cliente.get("/api/v1/datasets/agricultura?limite=0", headers=CABECERA_VALIDA)
    assert respuesta.status_code == 422


def test_agricultura_sin_token_da_401():
    respuesta = cliente.get("/api/v1/datasets/agricultura")
    assert respuesta.status_code == 401


def test_agricultura_con_token_incorrecto_da_401():
    cabecera_mala = {"Authorization": "Bearer token-inventado-que-no-sirve"}
    respuesta = cliente.get("/api/v1/datasets/agricultura", headers=cabecera_mala)
    assert respuesta.status_code == 401
