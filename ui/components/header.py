import customtkinter as ctk
from config import COLORS

class Header(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, height=50, corner_radius=10)
        self.app = app
        
        # Grid configuration
        self.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10,5))
        self.grid_columnconfigure(1, weight=1)
        
        # App title
        title_label = ctk.CTkLabel(
            self, 
            text="Calendario de clases de idiomas",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        # Status indicators frame
        self.status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.status_frame.grid(row=0, column=2, padx=20, pady=10, sticky="e")
        
        # Database status
        ctk.CTkLabel(
            self.status_frame, 
            text="BD:", 
            font=ctk.CTkFont(size=12)
        ).pack(side="left", padx=2)
        
        self.db_status = ctk.CTkLabel(
            self.status_frame,
            text="●",
            text_color=COLORS['error'],
            font=ctk.CTkFont(size=16)
        )
        self.db_status.pack(side="left", padx=2)
        
        # SharePoint status
        ctk.CTkLabel(
            self.status_frame,
            text="SP:",
            font=ctk.CTkFont(size=12)
        ).pack(side="left", padx=(10,2))
        
        self.sp_status = ctk.CTkLabel(
            self.status_frame,
            text="●",
            text_color=COLORS['error'],
            font=ctk.CTkFont(size=16)
        )
        self.sp_status.pack(side="left", padx=2)
        
        # Last sync time
        self.last_sync_label = ctk.CTkLabel(
            self.status_frame,
            text="Last sync: Never",
            font=ctk.CTkFont(size=12)
        )
        self.last_sync_label.pack(side="left", padx=(20,0))
    
    def update_db_status(self, connected: bool):
        """Update database connection status indicator"""
        self.db_status.configure(
            text_color=COLORS['success'] if connected else COLORS['error']
        )
    
    def update_sp_status(self, connected: bool):
        """Update SharePoint connection status indicator"""
        self.sp_status.configure(
            text_color=COLORS['success'] if connected else COLORS['error']
        )
    
    def update_last_sync(self, time: str):
        """Update last sync time"""
        self.last_sync_label.configure(text=f"Last sync: {time}")