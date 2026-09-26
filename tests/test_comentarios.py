from fastapi.testclient import TestClient

from app.config import get_settings
from app.errors import ErrorValleDataNoDisponible
from app.main import app
from app.services.valledata_client import ClienteValleDataFalso, get_cliente_valledata

cliente = TestClient(app)
CABECERA_VALIDA = {"Authorization": f"Bearer {get_settings().api_token}"}


def test_comentarios_devuelve_datos_falsos():
    respuesta = cliente.get("/api/v1/consume/bd_ckan/comments", headers=CABECERA_VALIDA)
    assert respuesta.status_code == 200

    cuerpo = respuesta.json()
    assert cuerpo["total"] == 4
    assert len(cuerpo["comentarios"]) == 4
    # En modo falso ningun municipio falla.
    assert cuerpo["municipios_con_error"] == []
    # Comentario crudo, con la misma forma que expone ValleData.
    assert set(cuerpo["comentarios"][0]) == {
        "id",
        "municipio",
        "dataset_id",
        "nombre_dataset",
        "usuario",
        "texto_es",
        "texto_en",
        "fecha",
    }


def test_comentarios_acepta_usuario_anonimo():
    # ValleData envia usuario=null en comentarios anonimos: DataGov debe transportarlo
    # sin romper (antes exigia usuario obligatorio).
    comentarios = cliente.get("/api/v1/consume/bd_ckan/comments", headers=CABECERA_VALIDA).json()["comentarios"]
    assert any(c["usuario"] is None for c in comentarios)


def test_comentarios_filtra_por_fecha():
    # El falso tiene guacari en 2026-08-19; los demas en 08-20/08-21. Con desde=2026-08-20
    # se excluye guacari -> 3 comentarios. Confirma que `desde` se aplica.
    respuesta = cliente.get(
        "/api/v1/consume/bd_ckan/comments?desde=2026-08-20", headers=CABECERA_VALIDA
    )
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["total"] == 3
    assert all(c["municipio"] != "guacari" for c in cuerpo["comentarios"])


def test_comentarios_desde_invalido_da_422():
    respuesta = cliente.get(
        "/api/v1/consume/bd_ckan/comments?desde=ayer", headers=CABECERA_VALIDA
    )
    assert respuesta.status_code == 422


def test_comentarios_requiere_token():
    respuesta = cliente.get("/api/v1/consume/bd_ckan/comments")
    assert respuesta.status_code == 401


def test_comentarios_si_valledata_falla_devuelve_502():
    # Simulamos que ValleData no responde: el cliente lanza ErrorValleDataNoDisponible.
    # El manejador debe traducirlo a un 502 limpio, no a un 500 feo.
    class ClienteQueFalla:
        def obtener_comentarios(self, desde=None):
            raise ErrorValleDataNoDisponible("conexion rechazada")

    app.dependency_overrides[get_cliente_valledata] = lambda: ClienteQueFalla()
    try:
        respuesta = cliente.get("/api/v1/consume/bd_ckan/comments", headers=CABECERA_VALIDA)
        assert respuesta.status_code == 502
        assert "ValleData" in respuesta.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_cliente_falso_entrega_comentarios_tipados():
    # Prueba directa del cliente falso, sin pasar por HTTP.
    comentarios, municipios_con_error = ClienteValleDataFalso().obtener_comentarios()
    assert len(comentarios) == 4
    assert comentarios[0].municipio == "alcala"
    assert municipios_con_error == []
