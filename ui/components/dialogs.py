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