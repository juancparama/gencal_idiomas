import os
import customtkinter as ctk
from datetime import datetime, date
import tkinter as tk
from tkcalendar import DateEntry
from tkinter import messagebox
import threading
from db import test_connection

from sharepoint import GraphDelegatedClient
from utils import load_festivos
from config import SP_CLIENT_ID, SP_TENANT_ID, USER_EMAIL, SP_SITE_HOST, SP_SITE_PATH, SP_LIST_NAME, COLORS

from ui.components.dialogs import ConfirmDialog
from ui.components.header import Header
from ui.components.config_panel import ConfigPanel
from ui.components.calendar_manager import CalendarManager
from ui.components.main_panel import MainPanel
from ui.components.statusbar_panel import StatusBar
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

        # Estado compartido        
        self.app_state = {
            "festivos": load_festivos(),
            "df_out": None,
            "dates": (None, None),
            "graph": None,
            "site_id": None,
            "list_id": None,
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
        self.sp_authenticated = False
        
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
    
    
    def authenticate_sharepoint(self):
        """Authenticate with SharePoint"""
        self.update_status("Authenticating with SharePoint...")
        self.log(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Authenticating with SharePoint")        
        self.status_bar.set_progress(0.5)

        def on_auth_complete():
            """Callback para cuando la autenticación es exitosa"""
            self.status_bar.set_progress(0.3)                    
            self.after(1000, self._complete_sp_auth)

        def run():            
            try:
                self.ensure_graph()
                result = self.resolve_site_list()
                if result[0] and result[1]:  # Si tenemos site_id y list_id
                    self.after(0, on_auth_complete)  # Ejecutar en el hilo principal
            except Exception as e:
                self.log(f"Error en autenticación: {str(e)}")
        
        threading.Thread(target=run, daemon=True).start()
      
        
        # Simulate authentication
        # self.after(2000, self._complete_sp_auth)
    
    def _complete_sp_auth(self):
        """Complete SharePoint authentication"""
        self.sp_authenticated = True
        self.header.sp_status.configure(text_color=COLORS['success'])
        self.update_status("SharePoint authentication successful")
        self.status_bar.set_progress(0)
    
    def generate_calendar(self):
        self.calendar_manager.generate_calendar()
    
    def _complete_calendar_generation(self):
        self.calendar_manager._complete_calendar_generation()
    
    def export_cal(self):
        self.calendar_manager.export_cal()
    
    def load_cal(self):
        self.calendar_manager.load_cal()
           
    def sync_to_sharepoint(self):
        """Sync data to SharePoint"""
        if not self.sp_authenticated:
            messagebox.showwarning("Sin autentificar.", "Por favor, autentifícate primero en Sharepoint")
            return
        
        if not self.class_data:
            messagebox.showinfo("Sin datos.", "Por favor, genera primero el calendario de clases")
            return
        
        # Confirmation dialog
        dialog = ConfirmDialog(self, "Confirmar acción", 
                              "Esta acción ELIMINARÁ todos los datos de la lista SharePoint y los reemplazará con el nuevo calendario. ¿Deseas continuar?",
                              self._perform_sync)
        self.wait_window(dialog)
    
    def _perform_sync(self):
        """Perform the actual sync operation"""
        self.update_status("Syncing to SharePoint...")
        self.status_bar.set_progress(0.1)
        
        # Simulate sync process
        for i in range(10):
            self.after(i * 200, lambda p=i: self.status_bar.set_progress((p + 1) / 10))
        
        self.after(2000, self._complete_sync)
    
    def _complete_sync(self):
        """Complete sync operation"""
        self.header.last_sync_label.configure(text=f"Last sync: {datetime.now().strftime('%H:%M:%S')}")
        self.update_status("Sync completed successfully")
        self.status_bar.set_progress(0)
        messagebox.showinfo("Sync Complete", "Data has been successfully synced to SharePoint")
    
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
    
    # ---- SharePoint helpers compartidos ----
    def ensure_graph(self):
        """Ensure graph client is initialized"""
        if self.app_state["graph"] is None:
            # Pasar la función add_log en lugar de la lista logs
            self.app_state["graph"] = GraphDelegatedClient(
                SP_CLIENT_ID, 
                SP_TENANT_ID, 
                USER_EMAIL, 
                self.log
            )
        return self.app_state["graph"]

    def resolve_site_list(self):
        site_graph_id = f"{SP_SITE_HOST}:{SP_SITE_PATH}"
        self.log(f"Resolviendo Site por ruta {site_graph_id}...")
        g = self.ensure_graph()
        sid = g.get_site_id_by_path(site_graph_id)

        if not sid:
            self.log("No se pudo resolver site_id")
            return None, None
        
        lid = g.get_list_id_by_name(sid, SP_LIST_NAME)
        if not lid:
            self.log(f"No se encontró la lista '{SP_LIST_NAME}'")
            return sid, None
        
        self.app_state["site_id"], self.app_state["list_id"] = sid, lid
        self.log(f"Conectado. SiteID={sid} | ListID={lid}")

         # Obtener y mostrar el número de items
        item_count = g.get_list_item_count(sid, lid)
        if item_count != -1:            
            self.log(f"La lista '{SP_LIST_NAME}' contiene actualmente {item_count} elementos.")

        return sid, lid

    
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