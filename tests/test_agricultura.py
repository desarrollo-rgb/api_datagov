from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app

cliente = TestClient(app)

# Cabecera con el token correcto, tomado de la configuracion (asi la prueba no depende
# de un valor escrito a mano: usa el mismo token que la app).
CABECERA_VALIDA = {"Authorization": f"Bearer {get_settings().api_token}"}


def test_agricultura_devuelve_datos_falsos():
    respuesta = cliente.get("/api/v1/dataset_valledata/gold_cultivos_valle_geo?limite=2", headers=CABECERA_VALIDA)
    assert respuesta.status_code == 200

    cuerpo = respuesta.json()
    assert cuerpo["identificador"] == "agricultura"
    assert cuerpo["total_devuelto"] == 2
    assert len(cuerpo["filas"]) == 2
    # Las 27 columnas de la tabla gold `gold_cultivos_valle_geo`.
    assert set(cuerpo["filas"][0]) == {
        "tipo_cultivo", "anio", "semestre", "codigo_municipio", "municipio",
        "latitud", "longitud", "altura_snm", "temperatura_media",
        "superficie_piso_calido_x", "superficie_piso_medio_x",
        "superficie_piso_frio_x", "superficie_piso_paramo_x",
        "codigo_cultivo", "nombre_cultivo", "hectareas_sembradas",
        "hectareas_cosechadas", "indice_oni", "latitud_dec", "longitud_dec",
        "distancia_cavasa_km", "wkt_geometry", "piso_predominante",
        "superficie_piso_calido_y", "superficie_piso_medio_y",
        "superficie_piso_frio_y", "superficie_piso_paramo_y",
    }


def test_agricultura_respeta_el_limite():
    respuesta = cliente.get("/api/v1/dataset_valledata/gold_cultivos_valle_geo?limite=1000", headers=CABECERA_VALIDA)
    assert respuesta.status_code == 200
    assert respuesta.json()["total_devuelto"] == 3


def test_agricultura_rechaza_limite_invalido():
    respuesta = cliente.get("/api/v1/dataset_valledata/gold_cultivos_valle_geo?limite=0", headers=CABECERA_VALIDA)
    assert respuesta.status_code == 422


def test_agricultura_sin_token_da_401():
    respuesta = cliente.get("/api/v1/dataset_valledata/gold_cultivos_valle_geo")
    assert respuesta.status_code == 401


def test_agricultura_con_token_incorrecto_da_401():
    cabecera_mala = {"Authorization": "Bearer token-inventado-que-no-sirve"}
    respuesta = cliente.get("/api/v1/dataset_valledata/gold_cultivos_valle_geo", headers=cabecera_mala)
    assert respuesta.status_code == 401
