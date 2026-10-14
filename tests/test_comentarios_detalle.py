from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app

cliente = TestClient(app)

CABECERA_VALIDA = {"Authorization": f"Bearer {get_settings().api_token}"}

RUTA = "/api/v1/expose/gold_valledata/valledata_api_comentarios_detalle"


def test_detalle_devuelve_datos_falsos():
    respuesta = cliente.get(f"{RUTA}?limite=2", headers=CABECERA_VALIDA)
    assert respuesta.status_code == 200

    cuerpo = respuesta.json()
    assert cuerpo["identificador"] == "comentarios_detalle"
    assert cuerpo["total_devuelto"] == 2
    assert len(cuerpo["filas"]) == 2
    assert set(cuerpo["filas"][0]) == {
        "id_comentario",
        "fecha_publicacion",
        "fecha_hora_publicacion",
        "id_municipio_dataset",
        "municipio",
        "dataset_id",
        "nombre_dataset",
        "sentimiento",
        "emocion",
        "texto_es",
    }


def test_detalle_respeta_el_limite():
    respuesta = cliente.get(f"{RUTA}?limite=1", headers=CABECERA_VALIDA)
    assert respuesta.status_code == 200
    assert respuesta.json()["total_devuelto"] == 1


def test_detalle_rechaza_limite_invalido():
    respuesta = cliente.get(f"{RUTA}?limite=0", headers=CABECERA_VALIDA)
    assert respuesta.status_code == 422


def test_detalle_sin_token_da_401():
    respuesta = cliente.get(RUTA)
    assert respuesta.status_code == 401


def test_detalle_filtra_por_municipio_sin_importar_mayusculas():
    # Los dos ejemplos son de ALCALA. Con "alcala" (minuscula) deben venir los 2.
    respuesta = cliente.get(f"{RUTA}?municipio=alcala", headers=CABECERA_VALIDA)
    assert respuesta.status_code == 200
    assert respuesta.json()["total_devuelto"] == 2
    # Un municipio sin comentarios -> 0.
    respuesta = cliente.get(f"{RUTA}?municipio=cerrito", headers=CABECERA_VALIDA)
    assert respuesta.json()["total_devuelto"] == 0


def test_detalle_filtra_por_fecha_y_hora():
    # id 144 es 14:33:32 y id 143 es 14:33:07 (ambos 2026-10-10). Con desde 14:33:20
    # solo queda el de las 14:33:32 -> 1.
    respuesta = cliente.get(
        f"{RUTA}?fecha_hora_publicacion=2026-10-10T14:33:20", headers=CABECERA_VALIDA
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["total_devuelto"] == 1


def test_detalle_filtra_por_fecha_sola():
    # Con la fecha sola (00:00) entran los dos; con el dia siguiente, ninguno.
    assert cliente.get(f"{RUTA}?fecha_hora_publicacion=2026-10-10", headers=CABECERA_VALIDA).json()["total_devuelto"] == 2
    assert cliente.get(f"{RUTA}?fecha_hora_publicacion=2026-10-11", headers=CABECERA_VALIDA).json()["total_devuelto"] == 0


def test_detalle_fecha_invalida_da_422():
    respuesta = cliente.get(f"{RUTA}?fecha_hora_publicacion=ayer", headers=CABECERA_VALIDA)
    assert respuesta.status_code == 422
