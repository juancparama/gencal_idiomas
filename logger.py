from datetime import datetime
import threading
import os

class AppLogger:
    LEVELS = {"INFO": "INFO", "WARNING": "WARNING", "ERROR": "ERROR"}

    def __init__(self, log_file: str = "app.log"):
        self.logs = []
        self.lock = threading.Lock()
        self.log_file = log_file
        # Crear fichero si no existe
        if not os.path.exists(log_file):
            with open(log_file, "w", encoding="utf-8") as f:
                f.write(f"{datetime.now()} - Log iniciado\n")

    def _format_entry(self, message: str, level: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"{timestamp} - {level} - {message}"

    def log(self, message: str, level: str = "INFO"):
        level = level.upper()
        if level not in self.LEVELS:
            level = "INFO"

        entry = self._format_entry(message, level)
        with self.lock:
            self.logs.append(entry)
            # Guardar en fichero
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(entry + "\n")
        return entry

    def info(self, message: str):
        return self.log(message, "INFO")

    def warning(self, message: str):
        return self.log(message, "WARNING")

    def error(self, message: str):
        return self.log(message, "ERROR")

    def get_logs(self):
        with self.lock:
            return self.logs.copy()
