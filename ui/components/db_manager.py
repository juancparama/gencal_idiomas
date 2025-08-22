import threading
from datetime import datetime
from tkinter import messagebox
from config import COLORS
from services.db_service import DatabaseService
import pandas as pd

class DatabaseManager:
    def __init__(self, app):
        self.app = app
        self.db_service = DatabaseService(log_callback=app.log)
        self.is_connected = False

    def test_connection(self):
        """Test database connection with UI feedback"""
        self.app.log(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Testing database connection")
        
        def test_process():
            try:
                if self.db_service.test_connection():
                    self.app.after(0, self._connection_success)
                else:
                    self.app.after(0, self._connection_failed)
            except Exception as e:
                self.app.log(f"Error en conexión: {str(e)}")
                self.app.after(0, lambda: self._connection_failed(str(e)))

        self.app.update_status("Probando la conexión a la base de datos...")
        self.app.status_bar.set_progress(0.3)
        threading.Thread(target=test_process, daemon=True).start()

    def _connection_success(self):
        """Handle successful connection"""
        self.is_connected = True
        self.app.header.db_status.configure(text_color=COLORS['success'])
        self.app.update_status("Conexión a la base de datos correcta")
        self.app.status_bar.set_progress(0)

    def _connection_failed(self, error_msg=None):
        """Handle failed connection"""
        self.is_connected = False
        self.app.header.db_status.configure(text_color=COLORS['error'])
        self.app.update_status("Error al conectar a la base de datos")
        self.app.status_bar.set_progress(0)
        if error_msg:
            messagebox.showerror("Error de conexión", f"Error conectando a la BD: {error_msg}")
    
    def ensure_connection(self) -> bool:
        """Ensure database connection is active"""
        if not self.is_connected:
            try:
                self.test_connection()
                return True
            except Exception:
                return False
        return True
    
    def read_clases(self, sql_query: str) -> pd.DataFrame:
        """Execute query with error handling and connection check"""
        if not self.ensure_connection():
            raise RuntimeError("No hay conexión activa con la base de datos")
        try:
            return self.db_service.read_clases(sql_query)
        except Exception as e:
            self.app.log(f"Error leyendo clases: {str(e)}")
            raise
