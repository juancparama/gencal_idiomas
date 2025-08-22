# File: services/excel_service.py
import tkinter as tk
from tkinter import filedialog
import pandas as pd

def exportar_calendario(df):
    if df is None or df.empty:
        return
    root = tk.Tk()
    root.withdraw()
    filepath = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Excel files", "*.xlsx")],
        initialfile="calendario.xlsx",
        title="Guardar calendario como"
    )
    if filepath:
        df.to_excel(filepath, index=False)
        return filepath
    return None

def cargar_calendario():
    root = tk.Tk()
    root.withdraw()
    filepath = filedialog.askopenfilename(
        title="Seleccionar archivo de calendario",
        filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
    )
    if filepath:
        return pd.read_excel(filepath)
    return None