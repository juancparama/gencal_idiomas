import customtkinter as ctk
from config import COLORS

class MainPanel(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, corner_radius=10)
        self.app = app
        
        # Setup grid
        self.grid(row=1, column=1, sticky="nsew", padx=(5,10), pady=10)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Headers for data grid
        self.headers = ["Título", "PERNR", "Nombre", "Mail", "Fecha", "Grupo", "Idioma"]
        
        # Create components
        self.setup_preview_header()
        self.setup_data_grid()
        self.setup_action_buttons()

    def setup_preview_header(self):
        """Create the preview section header with filters"""
        preview_header = ctk.CTkFrame(self, height=60, fg_color="transparent")
        preview_header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10,5))
        preview_header.grid_columnconfigure(1, weight=1)
        
        # Title
        ctk.CTkLabel(preview_header, 
                     text="Vista previa del calendario de clases",
                     font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, sticky="w", pady=10)
        
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

    def setup_data_grid(self):
        """Create the data grid for displaying class information"""
        self.data_frame = ctk.CTkScrollableFrame(self)
        self.data_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        # Create table header
        self.create_table_header()
                
        # Data rows container
        self.data_rows_frame = ctk.CTkFrame(self.data_frame, fg_color="transparent")
        self.data_rows_frame.pack(fill="both", expand=True)

    def create_table_header(self):
        """Create table headers"""
        header_frame = ctk.CTkFrame(self.data_frame, fg_color="gray25", height=40)
        header_frame.pack(fill="x", pady=(0,2))

        # Configure column weights
        for i in range(len(self.headers)):
            header_frame.grid_columnconfigure(i, weight=1)

        # Create header labels
        for i, header in enumerate(self.headers):
            ctk.CTkLabel(header_frame, 
                        text=header,
                        font=ctk.CTkFont(weight="bold"),
                        anchor="center",
                        justify="center"
            ).grid(row=0, column=i, padx=5, pady=8, sticky="nsew")

    def setup_action_buttons(self):
        """Create the action buttons panel"""
        action_frame = ctk.CTkFrame(self, height=80, fg_color="transparent")
        action_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        
        # Left side buttons
        left_frame = ctk.CTkFrame(action_frame, fg_color="transparent")
        left_frame.pack(side="left", pady=10)
        
        self.generate_btn = ctk.CTkButton(
            left_frame,
            text="Generar calendario",
            width=150, height=40,
            font=ctk.CTkFont(size=14),
            command=self.app.generate_calendar
        )
        self.generate_btn.pack(side="left", padx=5)

        self.export_btn = ctk.CTkButton(
            left_frame,
            text="Exportar calendario",
            width=150, height=40,
            fg_color=COLORS['warning'],
            hover_color="#E67E22",
            font=ctk.CTkFont(size=14),
            command=self.app.export_cal
        )
        self.export_btn.pack(side="left", padx=5)
        
        self.preview_btn = ctk.CTkButton(
            left_frame,
            text="Cargar calendario",
            width=150, height=40,
            fg_color=COLORS['warning'],
            hover_color="#E67E22",
            font=ctk.CTkFont(size=14),
            command=self.app.load_cal
        )
        self.preview_btn.pack(side="left", padx=5)
        
        # Right side button
        right_frame = ctk.CTkFrame(action_frame, fg_color="transparent")
        right_frame.pack(side="right", pady=10)
        
        self.sync_btn = ctk.CTkButton(
            right_frame,
            text="Subir a SharePoint",
            width=180, height=40,
            fg_color=COLORS['success'],
            hover_color="#27AE60",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.app.sync_to_sharepoint
        )
        self.sync_btn.pack(padx=5)

    def filter_data(self):
        """Filter data based on date range"""
        date_from = self.date_from.get().strip()
        date_to = self.date_to.get().strip()
        
        if date_from or date_to:
            self.app.update_status(f"Filtering data from {date_from} to {date_to}")
            self.refresh_data_grid()
        else:
            self.refresh_data_grid()

    def refresh_data_grid(self):
        """Refresh the data grid display"""
        for widget in self.data_rows_frame.winfo_children():
            widget.destroy()
        
        for i, row_data in enumerate(self.app.class_data):
            self.create_data_row(row_data, i)

    def create_data_row(self, row_data, row_index):
        """Create a single data row"""
        row_frame = ctk.CTkFrame(
            self.data_rows_frame,
            fg_color="gray20" if row_index % 2 == 0 else "gray15",
            height=35
        )
        row_frame.pack(fill="x", pady=1)
        
        filtered_data = row_data[:7]
        
        for i in range(len(self.headers)):
            row_frame.grid_columnconfigure(i, weight=1)
        
        for i, data in enumerate(filtered_data):
            label = ctk.CTkLabel(
                row_frame,
                text=str(data),
                font=ctk.CTkFont(size=12),
                anchor="center",
                justify="center"
            )
            label.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")

    def update_record_count(self, total_records):
        """Update the record count label"""
        if total_records > 10:
            self.record_count_label.configure(
                text=f"Vista previa (mostrando 10 de {total_records} registros)",
                text_color=COLORS['warning']
            )
        else:
            self.record_count_label.configure(
                text=f"Registros: {total_records}",
                text_color="white"
            )