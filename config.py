from dotenv import load_dotenv
import os

# Cargar .env desde la raíz del proyecto
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

DB_SERVER = os.getenv("DB_SERVER")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Consulta por defecto
CONSULTA = os.getenv("CONSULTA", "")

# Rutas de salida
OUTPUT_FILE = os.getenv("OUTPUT_FILE", "calendario_clases.xlsx")

# JSON festivos
FESTIVOS_JSON = os.getenv("FESTIVOS_JSON", "festivos.json")
