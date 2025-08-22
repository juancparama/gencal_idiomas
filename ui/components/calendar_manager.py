import customtkinter as ctk
from datetime import datetime
from tkinter import messagebox
from config import OUTPUT_FILE, CONSULTA
from utils import exportar_calendario, cargar_calendario
from services.calendar_service import CalendarService
import pandas as pd

class CalendarManager:
    def __init__(self, app):
        """
        Initialize calendar manager
        Args:
            app: Main application instance
        """
        self.app = app
        self.calendar_service = CalendarService(
            self.app.db_manager.db_service,
            log_callback=self.app.log
        )

    def generate_calendar(self):
        """Generate calendar with UI feedback"""
        try:
            # Verificar conexión BD
            self.app.db_manager.test_connection()
            
            # Obtener fechas
            start_str, end_str = self.app.fechas_panel.get_dates()
            if not start_str or not end_str:
                messagebox.showerror("Fechas requeridas", 
                                   "Debes introducir fecha inicio y fecha fin")
                return

            # Convertir fechas
            sd = datetime.strptime(start_str, "%Y-%m-%d")
            ed = datetime.strptime(end_str, "%Y-%m-%d")

            # Generar calendario
            self.app.update_status("Generando calendario desde la base de datos...")
            self.app.log(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Generando calendario")
            self.app.status_bar.set_progress(0.2)

            self.app.calendar_df = self.calendar_service.generate_calendar(
                start_date=sd,
                end_date=ed,
                sql_query=CONSULTA,
                festivos=self.app.holidays
            )

            # Completar generación
            self.app.after(1500, self._complete_calendar_generation)

        except Exception as e:
            self.app.update_status("Error al generar calendario")
            self.app.log(f"Error: {str(e)}")
            messagebox.showerror("Error", str(e))
            self.app.status_bar.set_progress(0)

    def _complete_calendar_generation(self):
        """Complete calendar generation"""
        self.app.load_sample_data()
        n_registros = len(self.app.calendar_df) if self.app.calendar_df is not None else 0
        self.app.update_status("Calendario generado correctamente")
        self.app.log(
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Calendario generado correctamente ({n_registros} registros)"
        )
        self.app.status_bar.set_progress(0)

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