"""Configuracion comun de las pruebas.

Se ejecuta ANTES de importar la app. Fuerza el modo "falso" para TODAS las pruebas: asi
los tests son deterministas y no dependen del .env de desarrollo ni de infraestructura
real (BigQuery, ValleData). Las variables de entorno mandan sobre el archivo .env.
"""

import os

# Modo falso, pase lo que pase en el .env local.
os.environ["USAR_DATOS_FALSOS"] = "true"
os.environ["USAR_VALLEDATA_FALSO"] = "true"
# Token fijo para las pruebas (no dependemos del token real del .env).
os.environ["API_TOKEN"] = "token-de-pruebas"
