# File: ui/components/sharepoint_manager.py
import asyncio
import math
import threading
from datetime import datetime
from tkinter import messagebox
from config import COLORS
from services.sharepoint_service import SharePointService


class SharePointManager:
    def __init__(self, app):
        self.app = app        
        self.log_fn = app.log        
        self.sp_service = SharePointService(log_callback=app.log)
        
    def authenticate(self, on_success=None):
        """Start SharePoint authentication process"""
        self.app.update_status("Autenticando con SharePoint...")
        self.app.log(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Autenticando con SharePoint")
        self.app.status_bar.set_progress(0.5)

        def auth_process():
            try:
                if self.sp_service.authenticate():
                    self.app.after(0, lambda: self._complete_auth(on_success))
                else:
                    self.app.after(0, self._auth_failed)
            except Exception as e:
                self.app.log(f"Error en autenticación: {str(e)}")
                self.app.after(0, self._auth_failed)

        threading.Thread(target=auth_process, daemon=True).start()
    
    def _complete_auth(self, on_success=None):
        """Handle successful authentication"""
        self.app.sp_authenticated = True
        self.app.header.sp_status.configure(text_color=COLORS['success'])
        self.app.update_status("Autenticación SharePoint exitosa")
        self.app.status_bar.set_progress(0)

        if on_success:
            on_success()
    
    def _auth_failed(self):
        """Handle failed authentication"""
        self.app.sp_authenticated = False
        self.app.header.sp_status.configure(text_color=COLORS['error'])
        self.app.update_status("Error en autenticación SharePoint")
        self.app.status_bar.set_progress(0)
        messagebox.showwarning("Autenticación fallida", "No se pudo autenticar en SharePoint. Inténtalo de nuevo.")

    def sync_to_sharepoint(self):
        """Initialize SharePoint sync process"""

        def continue_sync():
            if not self.app.class_data:
                messagebox.showinfo("Sin datos", "Por favor, genera primero el calendario de clases")
                return
                        
            answer = messagebox.askyesnocancel(
                "Sincronizar con SharePoint",
                "¿Qué deseas hacer?\n\n"
                "Crear calendario nuevo\n"
                "Actualizar el calendario\n"
                "Cancelar"
            )
            if answer is None:
                return  # cancelado por el usuario

            mode = "replace" if answer is True else "update"
            self._perform_sync(mode)

        # Lanzamos autenticación, y si funciona → ejecuta continue_sync
        self.authenticate(on_success=continue_sync)
    
    def _perform_sync(self, mode: str):
        """Execute the sync operation in the chosen mode ('replace' or 'update')"""
        self.app.update_status("Sincronizando con SharePoint...")
        self.app.status_bar.set_progress(0.1)

        if not self.app.class_data:
            self.app.log("⚠️ No hay registros en class_data para insertar.")
            return

        self.app.log(f"📊 Registros a procesar: {len(self.app.class_data)} | modo = {mode}")

        # Sanitizar valores: reemplazamos NaN por None
        clean_data = [
            {k: (None if (isinstance(v, float) and math.isnan(v)) else v) for k, v in row.items()}
            for row in self.app.class_data
        ]

        def sync_process():
            try:                
                ok = self.sp_service.sync_data(clean_data, mode=mode)
                if ok:
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
    

    def delete_all_items(self):
        """Autentica y borra todos los elementos de la lista SharePoint"""
        def continue_delete():
            self.app.update_status("Borrando todos los elementos de SharePoint...")
            self.app.status_bar.set_progress(0.3)

            def delete_process():
                try:
                    ok = asyncio.run(self.sp_service.delete_all_items_async())                    
                    if ok and self.sp_service.is_list_empty():
                        self.app.after(0, lambda: messagebox.showinfo("✅ Borrado verificado", "La lista está vacía."))
                    else:
                        self.app.after(0, lambda: messagebox.showwarning("⚠️ Verificación fallida", "La lista aún contiene elementos."))

                except Exception as e:
                    self.app.log(f"Error en borrado: {str(e)}")
                    self.app.after(0, lambda: messagebox.showerror("Error", f"No se pudo completar el borrado: {str(e)}"))
                finally:
                    self.app.status_bar.set_progress(0)

            threading.Thread(target=delete_process, daemon=True).start()

        self.authenticate(on_success=continue_delete)
