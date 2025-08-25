# File: ui/components/sharepoint_manager.py
import math
import threading
from datetime import datetime
from tkinter import messagebox
from config import COLORS
from ui.components.dialogs import ConfirmDialog
from services.sharepoint_service import SharePointService, insert_dataframe_in_batches

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

            dialog = ConfirmDialog(
                self.app,
                "Confirmar acción",
                "Esta acción ELIMINARÁ todos los datos de la lista SharePoint y los reemplazará con el nuevo calendario. ¿Deseas continuar?",
                self._perform_sync
            )
            self.app.wait_window(dialog)

        # Lanzamos autenticación, y si funciona → ejecuta continue_sync
        self.authenticate(on_success=continue_sync)


    def _perform_sync(self):
        """Execute the sync operation"""
        self.app.update_status("Sincronizando con SharePoint...")
        self.app.status_bar.set_progress(0.1)

        if not self.app.class_data:
            self.app.log("⚠️ No hay registros en class_data para insertar.")
            return

        self.app.log(f"📊 Registros a insertar en SharePoint: {len(self.app.class_data)}")

        # Sanitizar valores: reemplazamos NaN por None
        clean_data = [
            {k: (None if (isinstance(v, float) and math.isnan(v)) else v) for k, v in row.items()}
            for row in self.app.class_data
        ]

        def sync_process():
            try:
                if self.sp_service.sync_data(clean_data):
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
    
    def test_single_insert(self):
        """Inserta un registro de prueba válido en SharePoint"""
        if not self.sp_service.authenticate():
            self.log_fn("❌ No se pudo autenticar")
            return

        col_map = self.sp_service.get_column_map()
        if not col_map:
            self.log_fn("❌ No se pudo obtener el mapa de columnas")
            return

        test_row = {
            "Title": "Prueba",
            "PERNR": "000123",
            "Nombre": "Juan Pérez",
            "Mail": "juan.perez@example.com",
            "Fecha": "2025-08-25",
            "Grupo": "A",
            "Idioma": "Español"
        }

        # Mapear a internal names usando tu método tal como está
        mapped = self.sp_service._map_rows_to_internal([test_row], col_map)

        # 🔹 Corregir el Title: asegurarse que se use la columna interna 'Title'
        for row in mapped:
            if "LinkTitle" in row:
                row["Title"] = row.pop("LinkTitle")

        # Insertar usando batch (solo 1 registro)
        insert_dataframe_in_batches(
            self.sp_service.client,
            self.sp_service._site_id,
            self.sp_service._list_id,
            mapped,
            log=self.log_fn,
            batch_size=1
        )