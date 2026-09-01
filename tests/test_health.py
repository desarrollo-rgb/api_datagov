from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)


def test_health_responde_vivo():
    respuesta = cliente.get("/health")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "alive"}


def test_ready_en_modo_datos_falsos_esta_listo():
    respuesta = cliente.get("/ready")
    assert respuesta.status_code == 200
    assert respuesta.json()["status"] == "ready"


def test_salud_es_publica_sin_token():
    # Ninguno de los dos debe exigir cabecera de autorizacion.
    assert cliente.get("/health").status_code == 200
    assert cliente.get("/ready").status_code == 200
