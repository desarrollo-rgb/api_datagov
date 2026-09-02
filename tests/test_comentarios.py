from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.services.valledata_client import ClienteValleDataFalso

cliente = TestClient(app)
CABECERA_VALIDA = {"Authorization": f"Bearer {get_settings().api_token}"}


def test_comentarios_devuelve_datos_falsos():
    respuesta = cliente.get("/api/v1/comentarios", headers=CABECERA_VALIDA)
    assert respuesta.status_code == 200

    cuerpo = respuesta.json()
    assert cuerpo["total"] == 4
    assert len(cuerpo["comentarios"]) == 4
    # Comentario crudo, con la misma forma que expone ValleData.
    assert set(cuerpo["comentarios"][0]) == {
        "id",
        "municipio",
        "dataset_id",
        "usuario",
        "texto_es",
        "texto_en",
        "fecha",
    }


def test_comentarios_requiere_token():
    respuesta = cliente.get("/api/v1/comentarios")
    assert respuesta.status_code == 401


def test_cliente_falso_entrega_comentarios_tipados():
    # Prueba directa del cliente falso, sin pasar por HTTP.
    comentarios = ClienteValleDataFalso().obtener_comentarios()
    assert len(comentarios) == 4
    assert comentarios[0].municipio == "alcala"
