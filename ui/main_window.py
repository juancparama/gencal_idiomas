# File: ui/main_window.py
import customtkinter as ctk
import tkinter as tk

from services.holiday_service import load_festivos

from ui.components.dialogs import ConfirmDialog
from ui.components.header import Header
from ui.components.config_panel import ConfigPanel
from ui.components.calendar_manager import CalendarManager
from ui.components.main_panel import MainPanel
from ui.components.statusbar_panel import StatusBar
from ui.components.db_manager import DatabaseManager
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
        self.db_manager = DatabaseManager(self)
        self.calendar_manager = CalendarManager(self)
        self.sp_manager = SharePointManager(self)
        
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
        # self.db_connected = False
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
        self.db_manager.test_connection()
        
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
        """Load data from calendar_df and show a preview in the grid"""        
        if self.calendar_df is not None and not self.calendar_df.empty:
            # Convertimos todo el dataframe a lista de diccionarios para class_data
            self.class_data = self.calendar_df.to_dict(orient="records")
            
            # Preview para la grid: solo los primeros 10 registros
            preview_data = self.class_data[:10]
            self.main_panel.update_record_count(len(self.class_data))
        else:
            self.class_data = []
            preview_data = []
            self.main_panel.update_record_count(0)

        self.main_panel.refresh_data_grid(preview_data)
        
        
    def update_status(self, message: str):
        """Update status bar message"""
        self.status_bar.update_status(message)
    
    def on_window_resize(self, event):
        """Handle window resize events"""
        if event.widget == self:
            width = self.winfo_width()
            if width < 1200:
                # Adjust layout for smaller windows
                self.config_panel.configure(width=300)
            else:
                self.config_panel.configure(width=350)