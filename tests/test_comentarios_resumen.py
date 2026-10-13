from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app

cliente = TestClient(app)

CABECERA_VALIDA = {"Authorization": f"Bearer {get_settings().api_token}"}

RUTA = "/api/v1/expose/gold_valledata/valledata_api_comentarios_resumen_dataset"


def test_resumen_devuelve_datos_falsos():
    respuesta = cliente.get(f"{RUTA}?limite=2", headers=CABECERA_VALIDA)
    assert respuesta.status_code == 200

    cuerpo = respuesta.json()
    assert cuerpo["identificador"] == "comentarios_resumen_dataset"
    assert cuerpo["total_devuelto"] == 2
    assert len(cuerpo["filas"]) == 2
    assert set(cuerpo["filas"][0]) == {
        "id_municipio_dataset",
        "municipio",
        "dataset_id",
        "nombre_dataset",
        "total_comentarios",
        "comentarios_analizados",
        "positivos",
        "negativos",
        "neutros",
        "porcentaje_positivos",
        "porcentaje_negativos",
        "porcentaje_neutros",
        "indice_sentimiento",
        "sentimiento_predominante",
        "frustracion",
        "enojo",
        "disgusto",
        "miedo",
        "tristeza",
        "sorpresa",
        "confianza",
        "gratitud",
        "alegria",
        "neutral",
        "emocion_predominante",
        "porcentaje_emocion_predominante",
        "fecha_primer_comentario",
        "fecha_ultimo_comentario",
        "comentarios_ultimos_30_dias",
        "fecha_ultimo_analisis",
    }


def test_resumen_respeta_el_limite():
    respuesta = cliente.get(f"{RUTA}?limite=1", headers=CABECERA_VALIDA)
    assert respuesta.status_code == 200
    assert respuesta.json()["total_devuelto"] == 1


def test_resumen_rechaza_limite_invalido():
    respuesta = cliente.get(f"{RUTA}?limite=0", headers=CABECERA_VALIDA)
    assert respuesta.status_code == 422


def test_resumen_sin_token_da_401():
    respuesta = cliente.get(RUTA)
    assert respuesta.status_code == 401
