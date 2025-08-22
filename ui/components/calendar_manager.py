import customtkinter as ctk
from datetime import datetime, timedelta
from tkinter import messagebox
from config import OUTPUT_FILE, CONSULTA
from utils import exportar_calendario, cargar_calendario
from db import test_connection, read_clases
import pandas as pd


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

        start_str, end_str = self.app.fechas_panel.get_dates()

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

def generar_calendario(start_date, end_date, festivos=None):
    """Genera un calendario de clases entre dos fechas, excluyendo festivos."""

    try:
        sd = start_date
        ed = end_date        
        if sd > ed:
            messagebox.showerror("Error", "La fecha inicio debe ser anterior o igual a fecha fin.")
            return

        sql = CONSULTA
        df = read_clases(sql_query=sql)
        if df.empty:
            messagebox.showwarning("Atención", "La consulta no devolvió filas.")
            return

        df_out = generate_calendar_from_df(df, sd, ed, festivos)        

        return df_out
        # respuesta = messagebox.askyesno(
        #     "Éxito",
        #     "Calendario generado correctamente.\n\nAccede a Power Automate y ejecuta el flujo 'Generar calendario de idiomas' para completar el proceso.\n\n¿Deseas acceder ahora?"
        # )
        # if respuesta:
        #     webbrowser.open("https://make.powerautomate.com/environments/Default-37cd273a-1cec-4aae-a297-41480ea54f8d/flows/79f9731a-8a31-4d61-9529-f749f2ac723d/details")
        # messagebox.showinfo("Éxito", f"Calendario generado en '{OUTPUT_FILE}' ({len(df_out)} registros).")

    except Exception as e:
        messagebox.showerror("Error", str(e))

def generate_calendar_from_df(df_clases, start_date, end_date, festivos=None):
    festivos_set = set(festivos or [])
    rows = []
    start = pd.to_datetime(start_date).normalize()
    end = pd.to_datetime(end_date).normalize()

    for _, r in df_clases.iterrows():
        dia = int(r["Dia"])  # 1..5: lunes a viernes
        current = start
        while current <= end:
            if current.isoweekday() == dia and current.strftime("%Y-%m-%d") not in festivos_set:                
                base_date = pd.Timestamp('1900-01-01')
                numero_dia = (current - base_date).days + 2
                titulo = f"{r['PERNR']}-{numero_dia}"
                rows.append({
                    "Título": titulo,
                    "PERNR": r["PERNR"],
                    "Nombre": r["Nombre"],
                    "Mail": r["Mail"],
                    "Fecha": current.strftime("%Y-%m-%d"),
                    "Grupo": r["Grupo"],
                    "Idioma": r["Idioma"],
                    "Estado": "Pendiente",
                    "Aviso24h": "",
                    "Comentarios": ""
                })
            current += timedelta(days=1)

    df_out = pd.DataFrame(rows, columns=["Título","PERNR","Nombre","Mail","Fecha","Grupo","Idioma","Estado","Aviso24h","Comentarios"])
    return df_out
