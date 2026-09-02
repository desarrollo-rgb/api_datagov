"""Modelos de datos (contrato) que usa la API.

`Comentario` es el contrato PROVISIONAL de lo que expone la API ValleData en el Flujo 2.
Segun lo definido por ahora, cada comentario trae tres campos. Cuando el equipo de
ValleData cierre el contrato definitivo, se ajusta aqui; como el resto del codigo depende
de este modelo (no de un diccionario suelto), el cambio queda contenido en un solo lugar.
"""

from pydantic import BaseModel


class Comentario(BaseModel):
    # Fecha del comentario en UTC, formato ISO 8601 (provisional: aun es texto).
    fecha: str
    # El texto del comentario del ciudadano.
    comentario: str
    # Clasificacion del comentario (p. ej. "positivo", "negativo", "neutro").
    clasificacion: str
