import customtkinter as ctk
from datetime import datetime
from tkinter import messagebox
from config import OUTPUT_FILE
from utils import exportar_calendario, cargar_calendario
from db import test_connection
from calendario import generar_calendario

class CalendarManager:
    def __init__(self, app):
        self.app = app
        self.calendar_df = None

    def generate_calendar(self):
        """Generate calendar from database"""
        self.app.log(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Testing database connection")
        try:
            self.app.update_status("Probando la conexión a la base de datos...")
            if test_connection():
                self.app.log(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Database connection successful")                        
                self.app.progress_bar.set(0.3)                    
                self.app.after(1000, self.app._complete_db_test)            
        except RuntimeError as e:
            self.app.update_status("Error al conectar a la base de datos")
            self.app.log(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Error al conectar a la BD: {str(e)}")
            messagebox.showerror("Error de conexión.", f"Fallo de conexión a la BD: {str(e)}")
            return

        start_str = self.app.start_picker.get().strip()
        end_str = self.app.end_picker.get().strip()

        if not start_str or not end_str:
            messagebox.showerror("Fechas requeridas", "Debes introducir fecha inicio y fecha fin")
            return

        # Si hay valores, convertirlos
        sd = datetime.strptime(start_str, "%Y-%m-%d").date()
        ed = datetime.strptime(end_str, "%Y-%m-%d").date()

        if sd > ed:
            messagebox.showerror("Error", "La fecha inicio debe ser anterior o igual a fecha fin.")
            return

        self.app.calendar_df = generar_calendario(sd, ed, festivos=self.app.holidays)
        
        if self.app.calendar_df is None:
            pass
        else:
            self.app.update_status("Generando calendario desde la base de datos...")
            self.app.log(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Generando calendario")
            self.app.progress_bar.set(0.2)            
            self.app.after(1500, self._complete_calendar_generation)

    def _complete_calendar_generation(self):
        """Complete calendar generation"""
        self.app.load_sample_data()
        n_registros = len(self.app.calendar_df) if self.app.calendar_df is not None else 0
        self.app.update_status("Calendario generado correctamente")
        self.app.log(
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Calendario generado correctamente ({n_registros} registros)"
        )
        self.app.progress_bar.set(0)

    def export_cal(self):
        """Export calendar to Excel"""
        if self.app.calendar_df is not None and not self.app.calendar_df.empty:
            exportar_calendario(self.app.calendar_df)
            self.app.update_status("Calendario exportado correctamente a Excel")
            self.app.log(
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Calendario exportado correctamente a {OUTPUT_FILE}."
            )
        else:
            messagebox.showinfo("Sin datos.", "Por favor, genera primero el calendario de clases")
            return

    def load_cal(self):
        """Preview changes that will be made to SharePoint"""
        self.app.calendar_df = cargar_calendario()
        if self.app.calendar_df is None or self.app.calendar_df.empty:
            messagebox.showerror("Error", "No se pudo cargar el calendario desde el fichero Excel.")
            return
        self.app.update_status("Calendario cargado desde fichero Excel")
        self.app.log("Calendario cargado desde fichero Excel")
        self.app.load_sample_data()