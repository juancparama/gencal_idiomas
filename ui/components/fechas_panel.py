import customtkinter as ctk
from tkcalendar import DateEntry

class FechasPanel(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(
            parent,
            border_width=2,
            border_color="gray",
            corner_radius=10,
            fg_color="transparent"
        )
        self.app = app
        
        self.setup_fechas_panel()
        
    def setup_fechas_panel(self):
        """Create date range selection panel"""
        self.pack(fill="x", padx=10, pady=(0, 10), expand=True)

        # Section header
        ctk.CTkLabel(
            self,
            text="Fechas del calendario",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(10, 5))

        # Add fechas controls
        add_frame = ctk.CTkFrame(self, fg_color="transparent")
        add_frame.pack(fill="x", padx=10, pady=5)

        # Start date
        self.start_entry = ctk.CTkLabel(add_frame, text="Fecha inicio")
        self.start_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.start_picker = DateEntry(add_frame, date_pattern="yyyy-mm-dd")
        self.start_picker.delete(0, "end")
        self.start_picker.pack(side="left", fill="x", expand=True, padx=(0, 5))

        # End date
        self.end_entry = ctk.CTkLabel(add_frame, text="Fecha fin")
        self.end_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.end_picker = DateEntry(add_frame, date_pattern="yyyy-mm-dd")
        self.end_picker.delete(0, "end")
        self.end_picker.pack(side="left", fill="x", expand=True, padx=(0, 5))

    def get_date_range(self):
        """Get selected start and end dates"""
        start_date = self.start_picker.get_date()
        end_date = self.end_picker.get_date()
        return start_date, end_date

    def clear_dates(self):
        """Clear selected dates"""
        self.start_picker.delete(0, "end")
        self.end_picker.delete(0, "end")

    def get_dates(self) -> tuple[str, str]:
        """Get start and end dates as strings"""
        return (
            self.start_picker.get().strip(),
            self.end_picker.get().strip()
        )