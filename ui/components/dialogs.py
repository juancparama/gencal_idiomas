import customtkinter as ctk
import tkinter as tk
from config import COLORS

class ConfirmDialog(ctk.CTkToplevel):
    def __init__(self, parent, title, message, callback=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x200")
        self.transient(parent)
        self.callback = callback
        self.result = False
        
        # Center the dialog
        self.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        # Message
        ctk.CTkLabel(self, text=message, wraplength=350, font=ctk.CTkFont(size=14)).pack(pady=20)
        
        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        cancel_btn = ctk.CTkButton(btn_frame, text="Cancel", command=self.on_cancel)
        cancel_btn.pack(side="left", padx=10)
        
        confirm_btn = ctk.CTkButton(btn_frame, text="Confirm", fg_color=COLORS['error'], 
                                   hover_color="#C0392B", command=self.on_confirm)
        confirm_btn.pack(side="right", padx=10)
        
        self.after(10, self._set_grab)
    
    def _set_grab(self):
        """Set window grab after ensuring window is visible"""
        try:
            self.grab_set()
            self.focus_set()
        except tk.TclError:
            # If grab still fails, try again after a short delay
            self.after(50, self._set_grab)

    def on_cancel(self):
        self.result = False
        self.destroy()
    
    def on_confirm(self):
        self.result = True
        if self.callback:
            self.callback()
        self.destroy()

class SharePointDialog(ConfirmDialog):
    def __init__(self, parent, callback=None):
        # Llamamos al constructor original pero ponemos botones vacíos        
        super().__init__(parent, title="Sincronizar con SharePoint", message="¿Qué deseas hacer?", callback=callback)
        self.geometry("500x200")
        
        # Eliminamos los botones de Confirm / Cancel originales
        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                widget.destroy()
        
        # Nuevo frame de botones
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        def crear():
            self.result = "crear"
            if callback:
                callback("crear")
            self.destroy()

        def actualizar():
            self.result = "actualizar"
            if callback:
                callback("actualizar")
            self.destroy()

        def cancelar():
            self.result = None
            self.destroy()
        
        # Botones personalizados
        ctk.CTkButton(btn_frame, text="CREAR CALENDARIO", command=crear).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="ACTUALIZAR CALENDARIO", command=actualizar).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="CANCELAR", command=cancelar).pack(side="left", padx=10)

        # Centrar ventana
        self.center_window()
    
    def center_window(self):
        """Centra la ventana respecto a la ventana padre"""
        self.update_idletasks()  # Calcula tamaño real de la ventana
        w = self.winfo_width()
        h = self.winfo_height()
        parent_w = self.master.winfo_width()
        parent_h = self.master.winfo_height()
        parent_x = self.master.winfo_rootx()
        parent_y = self.master.winfo_rooty()
        x = parent_x + (parent_w - w) // 2
        y = parent_y + (parent_h - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")