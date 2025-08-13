# generator.py
from datetime import timedelta
import pandas as pd

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
                rows.append({
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

    df_out = pd.DataFrame(rows, columns=["PERNR","Nombre","Mail","Fecha","Grupo","Idioma","Estado","Aviso24h","Comentarios"])
    return df_out
