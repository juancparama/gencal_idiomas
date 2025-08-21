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

# Configuración de SharePoint
SP_CLIENT_ID = os.getenv("SP_CLIENT_ID")
SP_TENANT_ID = os.getenv("SP_TENANT_ID")
USER_EMAIL = os.getenv("USER_EMAIL")
SP_SITE_HOST = os.getenv("SP_SITE_HOST")
SP_SITE_PATH = os.getenv("SP_SITE_PATH")
SP_LIST_NAME = os.getenv("SP_LIST_NAME", "CalendarioClases")
SP_DATE_FIELD = os.getenv("SP_DATE_FIELD", "Fecha")

COLORS = {    
    'success': "#229150",
    'warning': '#F39C12', 
    'error': '#E74C3C',
    'info': '#3498DB',
    'neutral': '#95A5A6'
}
