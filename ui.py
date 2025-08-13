# ui.py
import customtkinter as ctk
from tkcalendar import DateEntry
from tkinter import messagebox, Listbox, END
from db import read_clases
from utils import load_festivos, save_festivos
from generator import generate_calendar_from_df
from config import OUTPUT_FILE, CONSULTA

def build_ui():
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")
    root = ctk.CTk()
    root.title("Generador de calendario de clases")
    root.geometry("720x520")

    top = ctk.CTkFrame(root)
    top.pack(padx=12, pady=8, fill="x")

    ctk.CTkLabel(top, text="Consulta SQL (usa CONSULTA del .env)").pack(anchor="w")
    sql_box = ctk.CTkTextbox(top, height=80)
    sql_box.insert("0.0", CONSULTA)
    sql_box.pack(fill="x", pady=6)

    frame_dates = ctk.CTkFrame(root)
    frame_dates.pack(padx=12, pady=6, fill="x")

    ctk.CTkLabel(frame_dates, text="Fecha inicio").grid(row=0, column=0, padx=6, pady=6, sticky="e")
    start_picker = DateEntry(frame_dates, date_pattern="yyyy-mm-dd")
    start_picker.grid(row=0, column=1, padx=6, pady=6)

    ctk.CTkLabel(frame_dates, text="Fecha fin").grid(row=1, column=0, padx=6, pady=6, sticky="e")
    end_picker = DateEntry(frame_dates, date_pattern="yyyy-mm-dd")
    end_picker.grid(row=1, column=1, padx=6, pady=6)

    frame_holidays = ctk.CTkFrame(root)
    frame_holidays.pack(padx=12, pady=6, fill="both", expand=False)
    ctk.CTkLabel(frame_holidays, text="Festivos (editable)").pack(anchor="w")

    # Usamos Listbox de tkinter
    listbox = Listbox(frame_holidays, height=6)
    festivos = load_festivos()
    for f in festivos:
        listbox.insert(END, f)
    listbox.pack(fill="x", pady=4)

    holiday_picker = DateEntry(frame_holidays, date_pattern="yyyy-mm-dd")
    holiday_picker.pack(side="left", padx=4)

    def add_holiday():
        fv = holiday_picker.get_date().strftime("%Y-%m-%d")
        if fv not in festivos:
            festivos.append(fv)
            listbox.insert(END, fv)
            save_festivos(festivos)

    def del_holiday():
        sel = listbox.curselection()
        if sel:
            item = listbox.get(sel[0])
            festivos.remove(item)
            listbox.delete(sel[0])
            save_festivos(festivos)

    ctk.CTkButton(frame_holidays, text="Añadir", command=add_holiday).pack(side="left", padx=4)
    ctk.CTkButton(frame_holidays, text="Eliminar", command=del_holiday).pack(side="left", padx=4)

    def generar_action():
        try:
            sd = start_picker.get_date()
            ed = end_picker.get_date()
            if sd > ed:
                messagebox.showerror("Error", "La fecha inicio debe ser anterior o igual a fecha fin.")
                return

            sql = sql_box.get("0.0", "end").strip() or CONSULTA
            df = read_clases(sql_query=sql)
            if df.empty:
                messagebox.showwarning("Atención", "La consulta no devolvió filas.")
                return

            df_out = generate_calendar_from_df(df, sd, ed, festivos)
            df_out.to_excel(OUTPUT_FILE, index=False)
            messagebox.showinfo("Éxito", f"Calendario generado en '{OUTPUT_FILE}' ({len(df_out)} registros).")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    ctk.CTkButton(root, text="Generar calendario", command=generar_action).pack(pady=12)

    return root
