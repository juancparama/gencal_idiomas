import os
import customtkinter as ctk
from datetime import datetime, date
import tkinter as tk
from tkcalendar import DateEntry
from tkinter import messagebox
import threading
from db import read_clases, test_connection
from calendario import generar_calendario
from sharepoint import GraphDelegatedClient
from utils import load_festivos, save_festivos, exportar_calendario, cargar_calendario
from config import SP_CLIENT_ID, SP_TENANT_ID, USER_EMAIL, SP_SITE_HOST, SP_SITE_PATH, SP_LIST_NAME, SP_DATE_FIELD, CONSULTA, OUTPUT_FILE, COLORS

from ui.components.dialogs import ConfirmDialog
from ui.components.header import Header
from ui.components.holiday_panel import HolidayPanel
from ui.components.calendar_manager import CalendarManager
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
        self.create_header()
        self.create_config_panel()
        self.create_main_content()
        self.create_status_bar()
        
        # Bind window resize event
        self.bind("<Configure>", self.on_window_resize)
        
        # Load sample data
        self.load_sample_data()
    
    def create_header(self):
        """Create the header with status indicators"""
        self.header = Header(self, self)
    
    def create_config_panel(self):
        """Create the configuration panel (left sidebar)"""
        self.config_frame = ctk.CTkScrollableFrame(self, width=350, corner_radius=10)
        self.config_frame.grid(row=1, column=0, sticky="nsew", padx=(10,5), pady=10)

        # Sección de conexiones
        self.create_conexiones_section()
        
        # Database Settings Section
        self.create_fechas_section()
        
        # Holiday Configuration Section
        self.create_holiday_section()

        # Logs Section
        self.create_log_section()
    
    def create_conexiones_section(self):
        """Create connections test section"""
        conexiones_section = ctk.CTkFrame(self.config_frame)
        conexiones_section.pack(fill="x", padx=10, pady=(0,10), expand=True)

        # Section header
        ctk.CTkLabel(conexiones_section, text="Conexiones",
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10,5))
        
        # Frame contenedor para los botones
        button_frame = ctk.CTkFrame(conexiones_section, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=(5,10))

        # Frame central para los botones
        center_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        center_frame.pack(expand=True, pady=5)

        # Test database connection button
        self.test_db_btn = ctk.CTkButton(center_frame, text="Test conexión BD",
                                        fg_color=COLORS['success'], hover_color="#27AE60",
                                        command=self.test_database_connection)
        self.test_db_btn.pack(side="left", padx=5)

        # Test SharePoint connection button
        self.test_sp_btn = ctk.CTkButton(center_frame, text="Test conexión Sharepoint",
                                        fg_color=COLORS['success'], hover_color="#27AE60",
                                        command=self.authenticate_sharepoint)
        self.test_sp_btn.pack(side="left", padx=5)
            

    def create_fechas_section(self):
        """Crear sección para definir las fechas del calendario"""
        fechas_section = ctk.CTkFrame(
            self.config_frame,
            border_width=2,          # grosor del borde
            border_color="gray",     # color del borde
            corner_radius=10,        # esquinas redondeadas
            fg_color="transparent"   # transparente para que resalte el borde
        )
        fechas_section.pack(fill="x", padx=10, pady=(0, 10), expand=True)

        # Section header
        ctk.CTkLabel(
            fechas_section,
            text="Fechas del calendario",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(10, 5))

        # Add fechas controls
        add_frame = ctk.CTkFrame(fechas_section, fg_color="transparent")
        add_frame.pack(fill="x", padx=10, pady=5)

        self.start_entry = ctk.CTkLabel(add_frame, text="Fecha inicio")
        self.start_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.start_picker = DateEntry(add_frame, date_pattern="yyyy-mm-dd")
        self.start_picker.delete(0, "end")
        self.start_picker.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.end_entry = ctk.CTkLabel(add_frame, text="Fecha fin")
        self.end_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.end_picker = DateEntry(add_frame, date_pattern="yyyy-mm-dd")
        self.end_picker.delete(0, "end")
        self.end_picker.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
    def create_holiday_section(self):
        """Create holiday configuration section"""
        self.holiday_panel = HolidayPanel(self.config_frame, self)
        self.holiday_panel.refresh_holiday_list()  # Llamar al refresh aquí
        
        
    def create_log_section(self):
        """Crear visor de logs en el panel de configuración"""
        log_section = ctk.CTkFrame(
            self.config_frame,
            border_width=2,
            border_color="gray",
            corner_radius=10,
            fg_color="transparent"
        )
        log_section.pack(fill="both", padx=10, pady=(0, 10), expand=True)

        ctk.CTkLabel(
            log_section,
            text="Visor de logs",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(10, 5))

        self.txt_log = ctk.CTkTextbox(
            log_section,
            width=300,
            height=150,
            state="disabled",
            wrap="word"
        )
        self.txt_log.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Configurar el widget en el log_manager
        self.log_manager.set_log_widget(self.txt_log)

        # Si hay logs anteriores, mostrarlos
        for entry in self.log_manager.logs:
            self.log_manager._append_to_log_box(entry)

    # ------------------------------
    # FUNCIÓN PRINCIPAL DE LOGS
    # ------------------------------
    def log(self, message: str):
        self.log_manager.log(message)

    def show_logs(self):
        self.log_manager.show_logs()

                  
    def create_main_content(self):
        """Create the main content area"""
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.grid(row=1, column=1, sticky="nsew", padx=(5,10), pady=10)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        # Preview section header
        self.create_preview_header()
        
        # Data grid
        self.create_data_grid()
        
        # Action buttons
        self.create_action_buttons()
    
    def create_preview_header(self):
        """Create the preview section header with filters"""
        preview_header = ctk.CTkFrame(self.main_frame, height=60, fg_color="transparent")
        preview_header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10,5))
        preview_header.grid_columnconfigure(1, weight=1)
        
        # Title
        ctk.CTkLabel(preview_header, text="Vista previa del calendario de clases", 
                    font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, sticky="w", pady=10)
        
        # Filter controls
        filter_frame = ctk.CTkFrame(preview_header, fg_color="transparent")
        filter_frame.grid(row=0, column=2, sticky="e", padx=10)
        
        ctk.CTkLabel(filter_frame, text="From:", font=ctk.CTkFont(size=12)).pack(side="left", padx=2)
        self.date_from = ctk.CTkEntry(filter_frame, placeholder_text="YYYY-MM-DD", width=100)
        self.date_from.pack(side="left", padx=2)
        
        ctk.CTkLabel(filter_frame, text="To:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(10,2))
        self.date_to = ctk.CTkEntry(filter_frame, placeholder_text="YYYY-MM-DD", width=100)
        self.date_to.pack(side="left", padx=2)
        
        filter_btn = ctk.CTkButton(filter_frame, text="Filter", width=60, height=28,
                                  command=self.filter_data)
        filter_btn.pack(side="left", padx=5)
        
        # Record count
        self.record_count_label = ctk.CTkLabel(preview_header, text="Registros: 0", 
                                              font=ctk.CTkFont(size=12))
        self.record_count_label.grid(row=1, column=0, sticky="w", pady=(0,5))
    
    def create_data_grid(self):
        """Create the data grid for displaying class information"""
        # Data display area
        self.data_frame = ctk.CTkScrollableFrame(self.main_frame)
        self.data_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        # Table headers from generator.py
        self.headers = ["Título", "PERNR", "Nombre", "Mail", "Fecha", "Grupo", "Idioma"]
        self.create_table_header()
                
        # Data rows container
        self.data_rows_frame = ctk.CTkFrame(self.data_frame, fg_color="transparent")
        self.data_rows_frame.pack(fill="both", expand=True)
    
    def create_table_header(self):
        """Create table headers"""
        header_frame = ctk.CTkFrame(self.data_frame, fg_color="gray25", height=40)
        header_frame.pack(fill="x", pady=(0,2))

        # Configurar el mismo peso para todas las columnas
        for i in range(len(self.headers)):
            header_frame.grid_columnconfigure(i, weight=1)

        for i, header in enumerate(self.headers):
            ctk.CTkLabel(header_frame, text=header, 
                        font=ctk.CTkFont(weight="bold"),
                        anchor="center",  # Centrar el texto
                        justify="center"  # Justificación central
            ).grid(row=0, column=i, padx=5, pady=8, sticky="nsew")  # sticky="nsew" para expandir en todas direcciones
    
    def create_action_buttons(self):
        """Create the action buttons panel"""
        action_frame = ctk.CTkFrame(self.main_frame, height=80, fg_color="transparent")
        action_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        
        # Left side buttons
        left_frame = ctk.CTkFrame(action_frame, fg_color="transparent")
        left_frame.pack(side="left", pady=10)
        
        self.generate_btn = ctk.CTkButton(left_frame, text="Generar calendario", 
                                         width=150, height=40, font=ctk.CTkFont(size=14),
                                         command=self.generate_calendar)
        self.generate_btn.pack(side="left", padx=5)

        self.export_btn = ctk.CTkButton(left_frame, text="Exportar calendario", 
                                        width=150, height=40, fg_color=COLORS['warning'], 
                                        hover_color="#E67E22", font=ctk.CTkFont(size=14),
                                        command=self.export_cal)
        self.export_btn.pack(side="left", padx=5)
        
        self.preview_btn = ctk.CTkButton(left_frame, text="Cargar calendario", 
                                        width=150, height=40, fg_color=COLORS['warning'], 
                                        hover_color="#E67E22", font=ctk.CTkFont(size=14),
                                        command=self.load_cal)
        self.preview_btn.pack(side="left", padx=5)
        
        # Right side button
        right_frame = ctk.CTkFrame(action_frame, fg_color="transparent")
        right_frame.pack(side="right", pady=10)
        
        self.sync_btn = ctk.CTkButton(right_frame, text="Subir a SharePoint", 
                                     width=180, height=40, fg_color=COLORS['success'], 
                                     hover_color="#27AE60", font=ctk.CTkFont(size=14, weight="bold"),
                                     command=self.sync_to_sharepoint)
        self.sync_btn.pack(padx=5)
    
    def create_status_bar(self):
        """Create the status bar with progress indicator"""
        self.status_frame = ctk.CTkFrame(self, height=60, corner_radius=10)
        self.status_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0,10))
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self.status_frame, width=400)
        self.progress_bar.pack(side="left", padx=20, pady=15)
        self.progress_bar.set(0)
        
        # Status text
        self.status_label = ctk.CTkLabel(self.status_frame, text="Ready", 
                                        font=ctk.CTkFont(size=12))
        self.status_label.pack(side="left", padx=10, pady=15)
        
        # Log button
        self.log_btn = ctk.CTkButton(self.status_frame, text="Show Logs", width=80, height=30,
                                    command=self.show_logs)
        self.log_btn.pack(side="right", padx=20, pady=15)
    
    # Event handlers and business logic methods
    
    
    def test_database_connection(self):
        """Test database connection"""
        self.log(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Testing database connection")
        if test_connection():
            self.update_status("Probando la conexión a la base de datos...")
            self.log(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Database connection successful")                        
            self.progress_bar.set(0.3)                    
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
        self.progress_bar.set(0)
    
    def authenticate_sharepoint(self):
        """Authenticate with SharePoint"""
        self.update_status("Authenticating with SharePoint...")
        self.log(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Authenticating with SharePoint")        
        self.progress_bar.set(0.5)

        def on_auth_complete():
            """Callback para cuando la autenticación es exitosa"""
            self.progress_bar.set(0.3)                    
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
        self.progress_bar.set(0)
    
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
        self.progress_bar.set(0.1)
        
        # Simulate sync process
        for i in range(10):
            self.after(i * 200, lambda p=i: self.progress_bar.set((p + 1) / 10))
        
        self.after(2000, self._complete_sync)
    
    def _complete_sync(self):
        """Complete sync operation"""
        self.header.last_sync_label.configure(text=f"Last sync: {datetime.now().strftime('%H:%M:%S')}")
        self.update_status("Sync completed successfully")
        self.progress_bar.set(0)
        messagebox.showinfo("Sync Complete", "Data has been successfully synced to SharePoint")
    
    def filter_data(self):
        """Filter data based on date range"""
        date_from = self.date_from.get().strip()
        date_to = self.date_to.get().strip()
        
        if date_from or date_to:
            self.update_status(f"Filtering data from {date_from} to {date_to}")
            # Here you would implement actual filtering logic
            self.refresh_data_grid()
        else:
            self.refresh_data_grid()
    
    def load_sample_data(self):        
        """Load data from calendar_df"""        
        if self.calendar_df is not None and not self.calendar_df.empty:            
            # Usar solo los 10 primeros registros para la vista previa
            preview_df = self.calendar_df.head(10)
            self.class_data = preview_df.values.tolist()
            # Mostrar mensaje de advertencia si hay más registros
            total_records = len(self.calendar_df)
            if total_records > 10:
                preview_message = f"Vista previa (mostrando 10 de {total_records} registros)"
                self.record_count_label.configure(
                    text=preview_message,
                    text_color=COLORS['warning']
                )
            else:
                self.record_count_label.configure(
                    text=f"Registros: {total_records}",
                    text_color="white"
                )
        else:
            self.class_data = []
            self.record_count_label.configure(
                text="Registros: 0",
                text_color="white"
            )

        self.refresh_data_grid()
        
    
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

    
    def update_status(self, message):
        """Update status bar message"""
        self.status_label.configure(text=message)
        self.update()
    
    def on_window_resize(self, event):
        """Handle window resize events"""
        if event.widget == self:
            width = self.winfo_width()
            if width < 1200:
                # Adjust layout for smaller windows
                self.config_frame.configure(width=300)
            else:
                self.config_frame.configure(width=350)