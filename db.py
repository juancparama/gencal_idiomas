# db.py
import pandas as pd
import urllib
from sqlalchemy import create_engine
from config import DB_SERVER, DB_NAME, DB_USER, DB_PASSWORD

def read_clases(sql_query: str) -> pd.DataFrame:
    """Lee datos desde SQL Server usando pandas y SQLAlchemy."""
    if not sql_query:
        raise ValueError("No se ha proporcionado ninguna consulta SQL.")

    params = urllib.parse.quote_plus(
        f"DRIVER={{SQL Server}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"UID={DB_USER};PWD={DB_PASSWORD}"
    )
    engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

    try:
        with engine.connect() as conn:
            df = pd.read_sql(sql_query, conn)
        return df
    except Exception as e:
        raise RuntimeError(f"Error al consultar la base de datos: {e}")