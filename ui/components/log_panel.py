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

        # Frame for title and button
        header_frame = ctk.CTkFrame(self)
        # header_frame.pack(fill="x", pady=(10, 5))
        header_frame.pack(fill="x", padx=5, pady=(10, 5))  # Added padx to frame

        # Title
        ctk.CTkLabel(
            header_frame,
            text="Visor de logs",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left", padx=10)

        # Log button
        self.log_btn = ctk.CTkButton(
            header_frame,
            text="Show Logs",
            width=80,
            height=30,
            command=self.app.show_logs
        )
        self.log_btn.pack(side="right", padx=20)

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