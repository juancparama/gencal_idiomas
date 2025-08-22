# File: ui/components/holiday_panel.py
import customtkinter as ctk
from datetime import datetime
from tkcalendar import DateEntry
from tkinter import messagebox
from config import COLORS
from services.holiday_service import save_festivos

class HolidayPanel(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(
            parent,
            border_width=2,
            border_color="gray",
            corner_radius=10,
            fg_color="transparent"
        )
        self.app = app
        self.holidays = app.holidays  # Referencia a la lista de festivos
        
        self.setup_holiday_panel()
        self.refresh_holiday_list()
        
    def setup_holiday_panel(self):
        """Create holiday configuration section"""
        self.pack(fill="x", padx=10, pady=(0,10), expand=True)
        
        # Section header
        ctk.CTkLabel(
            self, 
            text="Configuración de festivos",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(10,5))
        
        # Add holiday controls
        add_frame = ctk.CTkFrame(self, fg_color="transparent")
        add_frame.pack(fill="x", padx=10, pady=5)

        self.holiday_entry = DateEntry(add_frame, date_pattern="dd/MM/yyyy")
        self.holiday_entry.pack(side="left", fill="x", expand=True, padx=(0,5))
        
        add_btn = ctk.CTkButton(
            add_frame, 
            text="Add", 
            width=60, 
            height=28,
            command=self.add_holiday
        )
        add_btn.pack(side="right")
        
        # Holiday list
        ctk.CTkLabel(
            self, 
            text="Listado de festivos:", 
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=10, pady=(10,0))
        
        self.holiday_list_frame = ctk.CTkScrollableFrame(self, height=250)
        self.holiday_list_frame.pack(fill="both", expand=True, padx=10, pady=(5,10))
        
        # Quick presets
        preset_frame = ctk.CTkFrame(self, fg_color="transparent")
        preset_frame.pack(fill="x", padx=10, pady=(0,10))
        
        ctk.CTkButton(
            preset_frame, 
            text="Añadir festivos nacionales", 
            width=120, 
            height=28,
            command=self.add_es_holidays
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            preset_frame, 
            text="Borrar todos", 
            width=80, 
            height=28,
            fg_color=COLORS['error'], 
            hover_color="#C0392B",
            command=self.clear_holidays
        ).pack(side="right", padx=2)

    def add_holiday(self):
        """Add a holiday to the list"""
        holiday_date = self.holiday_entry.get().strip()  # Esto viene en DD/MM/YYYY

        if holiday_date:
            try:
                # Parsear DD/MM/YYYY a datetime
                fecha_obj = datetime.strptime(holiday_date, "%d/%m/%Y")
                # Convertir a YYYY-MM-DD para guardar
                holiday_iso = fecha_obj.strftime("%Y-%m-%d")

                if holiday_iso not in self.holidays:
                    self.holidays.append(holiday_iso)
                    self.holiday_entry.delete(0, 'end')
                    self.refresh_holiday_list()
                    save_festivos(self.holidays)
                    self.app.update_status(f"Añadido festivo: {holiday_date}") 
            except ValueError:
                messagebox.showerror(
                    "Fecha inválida", 
                    "Por favor, introduce una fecha en formato DD/MM/AAAA"
                )

    def refresh_holiday_list(self):
        """Refresh the holiday list display"""
        # Clear existing items
        for widget in self.holiday_list_frame.winfo_children():
            widget.destroy()
        
        # Add holiday items
        for i, holiday in enumerate(sorted(self.holidays)):
            item_frame = ctk.CTkFrame(
                self.holiday_list_frame, 
                fg_color="gray20" if i % 2 == 0 else "gray15"
            )
            item_frame.pack(fill="x", pady=1)

            # Convertir YYYY-MM-DD → DD/MM/YYYY
            try:
                fecha_obj = datetime.strptime(holiday, "%Y-%m-%d")
                fecha_str = fecha_obj.strftime("%d/%m/%Y")
            except ValueError:
                fecha_str = holiday  # fallback por si hay un valor raro
            
            ctk.CTkLabel(
                item_frame, 
                text=fecha_str
            ).pack(side="left", padx=10, pady=5)
            
            remove_btn = ctk.CTkButton(
                item_frame, 
                text="×", 
                width=30, 
                height=25,
                fg_color=COLORS['error'], 
                hover_color="#C0392B",
                command=lambda h=holiday: self.remove_holiday(h)
            )
            remove_btn.pack(side="right", padx=5, pady=2)

    def remove_holiday(self, holiday):
        """Remove a holiday from the list"""
        if holiday in self.holidays:
            self.holidays.remove(holiday)
            self.refresh_holiday_list()
            save_festivos(self.holidays)
            self.app.update_status(f"Eliminado festivo: {holiday}")

    def add_es_holidays(self):
        """Add common ES holidays"""
        es_holidays = [
            ("01-01", "Año Nuevo"),
            ("01-06", "Reyes Magos"),
            ("05-01", "Día del Trabajo"),
            ("08-15", "Asunción"),
            ("10-12", "Hispanidad"),
            ("11-01", "Todos los Santos"),
            ("12-06", "Constitución"),
            ("12-08", "Inmaculada"),
            ("12-25", "Navidad")
        ]

        # Obtener año actual
        current_year = datetime.now().year

        added = False
        for date, _ in es_holidays:
            full_date = f"{current_year}-{date}"
            if full_date not in self.holidays:
                self.holidays.append(full_date)
                added = True

        if added:
            self.refresh_holiday_list()
            save_festivos(self.holidays)
            self.app.update_status("Añadidos festivos nacionales para el año actual")

    def clear_holidays(self):
        """Clear all holidays"""
        if self.holidays:
            self.holidays.clear()
            self.refresh_holiday_list()
            save_festivos(self.holidays)
            self.app.update_status("Eliminados todos los festivos")