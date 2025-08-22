import customtkinter as ctk
from datetime import datetime

class LogManager:
    def __init__(self, app):
        self.app = app
        self.logs = []
        self.txt_log = None

    def set_log_widget(self, txt_log):
        """Set the text widget for displaying logs"""
        self.txt_log = txt_log

    def log(self, message: str):
        """Add a message to the list of logs and update viewer"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"{timestamp} - {message}"

        # Save to history
        self.logs.append(entry)

        # Update viewer if exists
        if self.txt_log is not None:
            # Ensure UI updates happen in the main thread
            self.app.after(0, lambda e=entry: self._append_to_log_box(e))

    def _append_to_log_box(self, entry: str):
        """Insert text in the log viewer"""
        if self.txt_log is None:
            return
        self.txt_log.configure(state="normal")
        self.txt_log.insert("end", entry + "\n")
        self.txt_log.see("end")
        self.txt_log.configure(state="disabled")

    def show_logs(self):
        """Show all logs in a separate window"""
        log_window = ctk.CTkToplevel(self.app)
        log_window.title("Application Logs")
        log_window.geometry("600x400")

        log_text = ctk.CTkTextbox(log_window, wrap="word")
        log_text.pack(fill="both", expand=True, padx=10, pady=10)

        log_text.configure(state="normal")
        for entry in self.logs:
            log_text.insert("end", entry + "\n")
        log_text.see("end")
        log_text.configure(state="disabled")