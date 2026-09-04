"""Modelos de datos (contrato) que usa la API.

`Comentario` es el comentario CRUDO tal como lo expone la API ValleData en el Flujo 2
(sin clasificar). La clasificacion de sentimiento NO vive en esta API: la agrega despues
el DAG y se guarda en BigQuery. DataGov solo transporta el comentario tal cual.

Debe coincidir con lo que ValleData expone. Al vivir en un solo lugar, si el contrato
cambia, el ajuste queda contenido aqui.
"""

from pydantic import BaseModel


class Comentario(BaseModel):
    # Id del comentario dentro de su municipio. NO es unico entre municipios:
    # la clave real es la combinacion municipio + id.
    id: int
    # Municipio de origen del comentario.
    municipio: str
    # Id del dataset comentado.
    dataset_id: str
    # Autor del comentario. Puede ser nulo: en CKAN los comentarios pueden ser
    # anonimos, asi que ValleData a veces envia usuario=null. Debe coincidir con
    # el contrato de ValleData.
    usuario: str | None
    # Texto del comentario separado por idioma.
    texto_es: str | None
    texto_en: str | None
    # Fecha de creacion en UTC, formato ISO 8601.
    fecha: str
