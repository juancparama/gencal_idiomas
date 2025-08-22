import customtkinter as ctk

class LogPanel(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(
            parent,
            border_width=2,
            border_color="gray",
            corner_radius=10,
            fg_color="transparent"
        )
        self.app = app
        self.setup_log_panel()

    def setup_log_panel(self):
        """Create log viewer panel"""
        self.pack(fill="both", padx=10, pady=(0, 10), expand=True)

        # Title
        ctk.CTkLabel(
            self,
            text="Visor de logs",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(10, 5))

        # Log text box
        self.txt_log = ctk.CTkTextbox(
            self,
            width=300,
            height=150,
            state="disabled",
            wrap="word"
        )
        self.txt_log.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Configure log manager
        self.app.log_manager.set_log_widget(self.txt_log)

        # Show existing logs if any
        for entry in self.app.log_manager.logs:
            self.app.log_manager._append_to_log_box(entry)