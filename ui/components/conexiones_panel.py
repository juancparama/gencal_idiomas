import customtkinter as ctk
from config import COLORS

class ConexionesPanel(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.pack(fill="x", padx=10, pady=(0,10), expand=True)
        
        self.setup_conexiones_panel()
        
    def setup_conexiones_panel(self):
        """Create connections test section"""
        # Section header
        ctk.CTkLabel(
            self,
            text="Conexiones",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(10,5))
        
        # Frame contenedor para los botones
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=(5,10))

        # Frame central para los botones
        center_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        center_frame.pack(expand=True, pady=5)

        # Test database connection button
        self.test_db_btn = ctk.CTkButton(
            center_frame,
            text="Test conexión BD",
            fg_color=COLORS['success'],
            hover_color="#27AE60",
            command=self.test_database
        )
        self.test_db_btn.pack(side="left", padx=5)

        # Test SharePoint connection button
        self.test_sp_btn = ctk.CTkButton(
            center_frame,
            text="Test conexión Sharepoint",
            fg_color=COLORS['success'],
            hover_color="#27AE60",
            command=self.test_sharepoint
        )
        self.test_sp_btn.pack(side="left", padx=5)

    def test_database(self):
        """Wrapper para el test de BD de la app"""
        self.app.test_database_connection()

    def test_sharepoint(self):
        """Wrapper para la autenticación de SharePoint de la app"""
        self.app.authenticate_sharepoint()