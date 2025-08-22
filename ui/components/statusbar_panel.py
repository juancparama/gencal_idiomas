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
        
        # Log button
        self.log_btn = ctk.CTkButton(
            self,
            text="Show Logs",
            width=80,
            height=30,
            command=self.app.show_logs
        )
        self.log_btn.pack(side="right", padx=20, pady=15)

    def update_status(self, message: str):
        """Update status message"""
        self.status_label.configure(text=message)
        self.status_label.update()

    def set_progress(self, value: float):
        """Set progress bar value (0-1)"""
        self.progress_bar.set(value)