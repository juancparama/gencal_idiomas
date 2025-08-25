from config import COLORS
import customtkinter as ctk

class StatusBar(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(
            parent,
            height=60,
            corner_radius=10
        )
        self.app = app
        
        # Grid configuration
        self.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0,10))
        
        self.setup_status_bar()

    def setup_status_bar(self):
        """Create the status bar components"""
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self, width=400)
        self.progress_bar.pack(side="left", padx=20, pady=15)
        self.progress_bar.set(0)
        
        # Status text
        self.status_label = ctk.CTkLabel(
            self,
            text="Ready",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(side="left", padx=10, pady=15)
        
        # # Log button
        # self.log_btn = ctk.CTkButton(
        #     self,
        #     text="Show Logs",
        #     width=80,
        #     height=30,
        #     command=self.app.show_logs
        # )
        # self.log_btn.pack(side="right", padx=20, pady=15)

        # Test SharePoint connection button
        self.test_sp_btn = ctk.CTkButton(
            self,
            text="Test conexión Sharepoint",
            width=80,
            height=30,            
            command=self.test_sharepoint
        )
        self.test_sp_btn.pack(side="right", padx=5)
        
        # Test database connection button
        self.test_db_btn = ctk.CTkButton(
            self,
            text="Test conexión BD",
            width=80,
            height=30,            
            command=self.test_database
        )
        self.test_db_btn.pack(side="right", padx=5)


    def update_status(self, message: str):
        """Update status message"""
        self.status_label.configure(text=message)
        self.status_label.update()

    def set_progress(self, value: float):
        """Set progress bar value (0-1)"""
        self.progress_bar.set(value)

    
    def test_database(self):
        """Wrapper para el test de BD de la app"""
        self.app.test_database_connection()

    def test_sharepoint(self):
        """Wrapper para la autenticación de SharePoint de la app"""
        self.app.authenticate_sharepoint()