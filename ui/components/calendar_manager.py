# File: ui/components/calendar_manager.py
from datetime import datetime
from tkinter import messagebox
from config import OUTPUT_FILE, CONSULTA
from services.calendar_service import CalendarService
from services.excel_service import exportar_calendario, cargar_calendario


class CalendarManager:
    def __init__(self, app):
        """
        Componente que conecta la UI con los servicios de calendario.
        """
        self.app = app
        self.service = CalendarService(
            db_service=self.app.db_manager.db_service,
            log_callback=self.app.log
        )

    def generate_calendar(self):
        """Generar calendario desde la BD"""
        try:
            # Verificar conexión a la BD
            self.app.db_manager.test_connection()

            # Obtener fechas desde UI
            start_str, end_str = self.app.config_panel.fechas_panel.get_dates()
            if not start_str or not end_str:
                messagebox.showerror("Fechas requeridas",
                                     "Debes introducir fecha inicio y fecha fin")
                return

            # Convertir fechas
            start = datetime.strptime(start_str, "%Y-%m-%d")
            end = datetime.strptime(end_str, "%Y-%m-%d")

            # Mostrar feedback
            self.app.update_status("Generando calendario desde la base de datos...")
            self.app.status_bar.set_progress(0.2)

            # Llamar al servicio
            self.app.calendar_df = self.service.generate_calendar(
                start_date=start,
                end_date=end,
                sql_query=CONSULTA,
                festivos=self.app.holidays
            )

            # Completar generación
            self.app.after(1000, self._complete_calendar_generation)

        except Exception as e:
            self.app.update_status("Error al generar calendario")
            self.app.log(f"Error: {str(e)}")
            messagebox.showerror("Error", str(e))
            self.app.status_bar.set_progress(0)

    def _complete_calendar_generation(self):
        """Finalizar la generación y refrescar UI"""
        n_registros = len(self.app.calendar_df) if self.app.calendar_df is not None else 0
        self.app.load_sample_data()
        self.app.update_status("Calendario generado correctamente")
        self.app.log(
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - "
            f"Calendario generado correctamente ({n_registros} registros)"
        )
        self.app.status_bar.set_progress(0)

    def export_cal(self):
        """Exportar calendario a Excel"""
        if self.app.calendar_df is not None and not self.app.calendar_df.empty:
            filepath = exportar_calendario(self.app.calendar_df)
            if filepath:
                self.app.update_status(f"Calendario exportado a {filepath}")
                self.app.log(
                    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - "
                    f"Calendario exportado correctamente a {filepath}."
                )
        else:
            messagebox.showinfo("Sin datos", "Por favor, genera primero el calendario de clases")

    def load_cal(self):
        """Cargar calendario desde Excel"""
        df = cargar_calendario()
        if df is None or df.empty:
            messagebox.showerror("Error", "No se pudo cargar el calendario desde el fichero Excel.")
            return
        self.app.calendar_df = df
        self.app.update_status("Calendario cargado desde fichero Excel")
        self.app.log("Calendario cargado desde fichero Excel")
        self.app.load_sample_data()