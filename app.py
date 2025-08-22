import os
import customtkinter as ctk
from datetime import datetime, date
import tkinter as tk
from tkcalendar import DateEntry
from tkinter import messagebox
import threading
from db import test_connection

from utils import load_festivos
from config import SP_CLIENT_ID, SP_TENANT_ID, USER_EMAIL, SP_SITE_HOST, SP_SITE_PATH, SP_LIST_NAME, COLORS

from ui.components.dialogs import ConfirmDialog
from ui.components.header import Header
from ui.components.config_panel import ConfigPanel
from ui.components.calendar_manager import CalendarManager
from ui.components.main_panel import MainPanel
from ui.components.statusbar_panel import StatusBar
from ui.components.sharepoint_manager import SharePointManager
from ui.utils.log_manager import LogManager


# Set appearance mode and color theme
ctk.set_appearance_mode("dark")  # "light", "dark", "system"
ctk.set_default_color_theme("dark-blue")  # "blue", "green", "dark-blue"


class SharePointSyncApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.calendar_df = None
        self.logs = []

        self.log_manager = LogManager(self)
        self.calendar_manager = CalendarManager(self)
        self.sp_manager = SharePointManager(self)

        # Estado compartido        
        self.app_state = {
            "festivos": load_festivos(),
            "df_out": None,
            "dates": (None, None),                                    
        }
        
        # Window configuration
        self.title("Calendario de clases de idiomas")
        self.geometry("1400x900")
        self.minsize(1000, 700)
        
        # Configure grid weights for responsive layout
        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Initialize data
        self.holidays = load_festivos()
        self.class_data = []
        self.db_connected = False
        # self.sp_authenticated = False
        
        # Create UI components
        self.header = Header(self, self)
        self.config_panel = ConfigPanel(self, self)
        self.main_panel = MainPanel(self, self)
        self.status_bar = StatusBar(self, self)
        
        # Bind window resize event
        self.bind("<Configure>", self.on_window_resize)
        
        # Load sample data
        self.load_sample_data()

    # ------------------------------
    # FUNCIÓN PRINCIPAL DE LOGS
    # ------------------------------
    def log(self, message: str):
        self.log_manager.log(message)

    def show_logs(self):
        self.log_manager.show_logs()


    # Event handlers and business logic methods
    def test_database_connection(self):
        """Test database connection"""
        self.log(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Testing database connection")
        if test_connection():
            self.update_status("Probando la conexión a la base de datos...")
            self.log(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Database connection successful")                        
            self.status_bar.set_progress(0.3)                    
            self.after(1000, self._complete_db_test)
        else:
            self.update_status("Error al conectar a la base de datos")
            self.log(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Database connection failed")
            messagebox.showerror("Connection Error", "Failed to connect to the database.")
    
    def _complete_db_test(self):
        """Complete database connection test"""
        self.db_connected = True
        self.header.db_status.configure(text_color=COLORS['success'])
        self.update_status("Conexión a la base de datos correcta")
        self.status_bar.set_progress(0)
    
    
    def generate_calendar(self):
        self.calendar_manager.generate_calendar()
    
    def _complete_calendar_generation(self):
        self.calendar_manager._complete_calendar_generation()
    
    def export_cal(self):
        self.calendar_manager.export_cal()
    
    def load_cal(self):
        self.calendar_manager.load_cal()
    
    def authenticate_sharepoint(self):
        self.sp_manager.authenticate()

    def sync_to_sharepoint(self):
        self.sp_manager.sync_to_sharepoint()
    
    def filter_data(self):
        """Filter data based on date range"""
        self.main_panel.filter_data()
    
    def load_sample_data(self):        
        """Load data from calendar_df"""        
        if self.calendar_df is not None and not self.calendar_df.empty:            
            # Usar solo los 10 primeros registros para la vista previa
            preview_df = self.calendar_df.head(10)

            self.class_data = preview_df.values.tolist()
            self.main_panel.update_record_count(len(self.calendar_df))
        else:
            self.class_data = []
            self.main_panel.update_record_count(0)

        self.main_panel.refresh_data_grid()
        
    
    def refresh_data_grid(self):
        """Refresh the data grid display"""
        # Clear existing rows
        for widget in self.data_rows_frame.winfo_children():
            widget.destroy()
        
        # Add data rows
        for i, row_data in enumerate(self.class_data):
            self.create_data_row(row_data, i)
        
        # Update record count
        # self.record_count_label.configure(text=f"Registros: {len(self.class_data)}")
    
    def create_data_row(self, row_data, row_index):
        """Create a single data row"""
        row_frame = ctk.CTkFrame(self.data_rows_frame, 
                                fg_color="gray20" if row_index % 2 == 0 else "gray15",
                                height=35)
        row_frame.pack(fill="x", pady=1)
        
        # row_frame.grid_columnconfigure(tuple(range(len(row_data))), weight=1)
        
         # Filtrar solo las columnas que queremos mostrar (primeras 7 columnas)
        filtered_data = row_data[:7]

        # Configurar el mismo peso para todas las columnas
        for i in range(len(self.headers)):
            row_frame.grid_columnconfigure(i, weight=1)
        
        # Crear las etiquetas con ancho fijo y alineación consistente
        for i, data in enumerate(filtered_data):
            label = ctk.CTkLabel(row_frame, 
                                text=str(data), 
                                font=ctk.CTkFont(size=12),
                                anchor="center",  # Centrar el texto
                                justify="center"  # Justificación central
            )
            label.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")  # sticky="nsew" para expandir en todas direcciones
        
    def update_status(self, message: str):
        """Update status bar message"""
        self.status_bar.update_status(message)
    
    def on_window_resize(self, event):
        """Handle window resize events"""
        if event.widget == self:
            width = self.winfo_width()
            if width < 1200:
                # Adjust layout for smaller windows
                self.config_frame.configure(width=300)
            else:
                self.config_frame.configure(width=350)