import json
from pathlib import Path
from config import FESTIVOS_JSON
import tkinter as tk
from tkinter import filedialog

# import webbrowser
# from db import read_clases
# from calendario import generate_calendar_from_df

# def generar_calendario(start_date, end_date, festivos=None):
#     """Genera un calendario de clases entre dos fechas, excluyendo festivos."""

#     try:
#         sd = start_date
#         ed = end_date        
#         if sd > ed:
#             messagebox.showerror("Error", "La fecha inicio debe ser anterior o igual a fecha fin.")
#             return

#         sql = CONSULTA
#         df = read_clases(sql_query=sql)
#         if df.empty:
#             messagebox.showwarning("Atención", "La consulta no devolvió filas.")
#             return

#         df_out = generate_calendar_from_df(df, sd, ed, festivos)
#         # df_out.to_excel(OUTPUT_FILE, index=False)

#         return df_out
#         # respuesta = messagebox.askyesno(
#         #     "Éxito",
#         #     "Calendario generado correctamente.\n\nAccede a Power Automate y ejecuta el flujo 'Generar calendario de idiomas' para completar el proceso.\n\n¿Deseas acceder ahora?"
#         # )
#         # if respuesta:
#         #     webbrowser.open("https://make.powerautomate.com/environments/Default-37cd273a-1cec-4aae-a297-41480ea54f8d/flows/79f9731a-8a31-4d61-9529-f749f2ac723d/details")
#         # messagebox.showinfo("Éxito", f"Calendario generado en '{OUTPUT_FILE}' ({len(df_out)} registros).")

#     except Exception as e:
#         messagebox.showerror("Error", str(e))

def exportar_calendario(df):
    """Exporta el DataFrame a un archivo Excel si no está vacío, pidiendo ruta con diálogo."""
    if df is None or df.empty:
        return  # No hay datos

    # Crear ventana raíz oculta
    root = tk.Tk()
    root.withdraw()  # Oculta la ventana principal

    # Abrir diálogo para seleccionar ruta y nombre del archivo
    filepath = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Excel files", "*.xlsx")],
        initialfile="calendario.xlsx",
        title="Guardar calendario como"
    )

    if filepath:  # Si el usuario no cancela
        df.to_excel(filepath, index=False)
        print(f"Calendario guardado en: {filepath}")

def load_festivos():
    p = Path(FESTIVOS_JSON)
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("festivos", [])

def save_festivos(festivos):
    p = Path(FESTIVOS_JSON)
    with p.open("w", encoding="utf-8") as f:
        json.dump({"festivos": festivos}, f, indent=2, ensure_ascii=False)
