# generator.py
from datetime import timedelta
import pandas as pd
from tkinter import messagebox
from config import CONSULTA
from db import read_clases

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
