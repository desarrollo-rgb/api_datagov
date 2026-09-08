from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app

cliente = TestClient(app)

CABECERA_VALIDA = {"Authorization": f"Bearer {get_settings().api_token}"}

RUTA = "/api/v1/expose/dataset_valledata/gold_pronostico_produccion"


def test_pronostico_devuelve_datos_falsos():
    respuesta = cliente.get(f"{RUTA}?limite=2", headers=CABECERA_VALIDA)
    assert respuesta.status_code == 200

    cuerpo = respuesta.json()
    assert cuerpo["identificador"] == "pronostico"
    assert cuerpo["total_devuelto"] == 2
    assert len(cuerpo["filas"]) == 2
    assert set(cuerpo["filas"][0]) == {
        "id_municipio",
        "id_cultivo",
        "fecha_proyectada",
        "produccion_estimada",
        "limite_inferior",
        "limite_superior",
    }


def test_pronostico_respeta_el_limite():
    respuesta = cliente.get(f"{RUTA}?limite=1000", headers=CABECERA_VALIDA)
    assert respuesta.status_code == 200
    assert respuesta.json()["total_devuelto"] == 3


def test_pronostico_rechaza_limite_invalido():
    respuesta = cliente.get(f"{RUTA}?limite=0", headers=CABECERA_VALIDA)
    assert respuesta.status_code == 422


def test_pronostico_sin_token_da_401():
    respuesta = cliente.get(RUTA)
    assert respuesta.status_code == 401
