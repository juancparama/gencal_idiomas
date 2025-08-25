import customtkinter as ctk
from ui.components.conexiones_panel import ConexionesPanel
from ui.components.fechas_panel import FechasPanel
from ui.components.holiday_panel import HolidayPanel
from ui.components.log_panel import LogPanel

class ConfigPanel(ctk.CTkScrollableFrame):
    def __init__(self, parent, app):
        super().__init__(
            parent,
            width=350,
            corner_radius=10
        )
        self.app = app
        
        # Configure grid
        self.grid(row=1, column=0, sticky="nsew", padx=(10,5), pady=10)
        
        # Create panels
        self.create_panels()

    def create_panels(self):
        """Create all configuration panels"""
        # Conexiones section
        # self.conexiones_panel = ConexionesPanel(self, self.app)
        
        # Fechas section
        self.fechas_panel = FechasPanel(self, self.app)
        
        # Holiday section
        self.holiday_panel = HolidayPanel(self, self.app)
        
        # Log section
        self.log_panel = LogPanel(self, self.app)