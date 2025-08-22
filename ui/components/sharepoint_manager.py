import threading
from datetime import datetime
from tkinter import messagebox
from config import COLORS
from ui.components.dialogs import ConfirmDialog
from services.sharepoint_service import SharePointService

class SharePointManager:
    def __init__(self, app):
        self.app = app
        self.sp_service = SharePointService(log_callback=app.log)
        
    def authenticate(self):
        """Start SharePoint authentication process"""
        self.app.update_status("Autenticando con SharePoint...")
        self.app.log(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Autenticando con SharePoint")
        self.app.status_bar.set_progress(0.5)
        
        def auth_process():
            try:
                if self.sp_service.authenticate():
                    self.app.after(0, self._complete_auth)
                else:
                    self.app.after(0, self._auth_failed)
            except Exception as e:
                self.app.log(f"Error en autenticación: {str(e)}")
                self.app.after(0, self._auth_failed)
        
        threading.Thread(target=auth_process, daemon=True).start()
    
    def _complete_auth(self):
        """Handle successful authentication"""
        self.app.sp_authenticated = True
        self.app.header.sp_status.configure(text_color=COLORS['success'])
        self.app.update_status("Autenticación SharePoint exitosa")
        self.app.status_bar.set_progress(0)
    
    def _auth_failed(self):
        """Handle failed authentication"""
        self.app.sp_authenticated = False
        self.app.header.sp_status.configure(text_color=COLORS['error'])
        self.app.update_status("Error en autenticación SharePoint")
        self.app.status_bar.set_progress(0)
    
    def sync_to_sharepoint(self):
        """Initialize SharePoint sync process"""
        if not self.sp_service.is_authenticated:
            messagebox.showwarning("Sin autentificar", "Por favor, autentifícate primero en SharePoint")
            return
            
        if not self.app.class_data:
            messagebox.showinfo("Sin datos", "Por favor, genera primero el calendario de clases")
            return
            
        dialog = ConfirmDialog(
            self.app,
            "Confirmar acción",
            "Esta acción ELIMINARÁ todos los datos de la lista SharePoint y los reemplazará con el nuevo calendario. ¿Deseas continuar?",
            self._perform_sync
        )
        self.app.wait_window(dialog)
    
    def _perform_sync(self):
        """Execute the sync operation"""
        self.app.update_status("Sincronizando con SharePoint...")
        self.app.status_bar.set_progress(0.1)
        
        def sync_process():
            try:
                if self.sp_service.sync_data(self.app.class_data):
                    self.app.after(0, self._complete_sync)
                else:
                    self.app.after(0, self._sync_failed)
            except Exception as e:
                self.app.log(f"Error en sincronización: {str(e)}")
                self.app.after(0, self._sync_failed)
        
        threading.Thread(target=sync_process, daemon=True).start()
    
    def _complete_sync(self):
        """Handle successful sync"""
        self.app.header.last_sync_label.configure(
            text=f"Last sync: {datetime.now().strftime('%H:%M:%S')}"
        )
        self.app.update_status("Sincronización completada")
        self.app.status_bar.set_progress(0)
        messagebox.showinfo("Sync Complete", "Datos sincronizados correctamente con SharePoint")
    
    def _sync_failed(self):
        """Handle failed sync"""
        self.app.update_status("Error en sincronización")
        self.app.status_bar.set_progress(0)
        messagebox.showerror("Error", "Error sincronizando datos con SharePoint")