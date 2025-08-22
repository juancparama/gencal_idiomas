import pandas as pd
import urllib
from sqlalchemy import create_engine
from config import DB_SERVER, DB_NAME, DB_USER, DB_PASSWORD

class DatabaseService:
    def __init__(self, log_callback=None):
        self.log_fn = log_callback or (lambda x: None)
        self._engine = None
        self._create_engine()

    def _create_engine(self):
        """Create SQLAlchemy engine with current config"""
        params = urllib.parse.quote_plus(
            f"DRIVER={{SQL Server}};"
            f"SERVER={DB_SERVER};"
            f"DATABASE={DB_NAME};"
            f"UID={DB_USER};PWD={DB_PASSWORD}"
        )
        self._engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self._engine.connect() as conn:
                self.log_fn("Conexión exitosa a la base de datos.")
                return True
        except Exception as e:
            error_msg = f"Error al conectar a la base de datos: {e}"
            self.log_fn(error_msg)
            raise RuntimeError(error_msg)

    def read_clases(self, sql_query: str) -> pd.DataFrame:
        """Execute query and return DataFrame"""
        if not sql_query:
            raise ValueError("No se ha proporcionado ninguna consulta SQL.")

        try:
            with self._engine.connect() as conn:
                df = pd.read_sql(sql_query, conn)
            return df
        except Exception as e:
            error_msg = f"Error al consultar la base de datos: {e}"
            self.log_fn(error_msg)
            raise RuntimeError(error_msg)

# Singleton instance for backwards compatibility
_default_service = DatabaseService()

def test_connection():
    """Legacy function for backwards compatibility"""
    return _default_service.test_connection()

def read_clases(sql_query: str) -> pd.DataFrame:
    """Legacy function for backwards compatibility"""
    return _default_service.read_clases(sql_query)