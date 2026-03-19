# src/utils/widgets.py

import tkinter as tk
from tkinter import ttk
from src.utils.helpers import lighten_color

class ModernButton(tk.Button):
    def __init__(self, master=None, theme_service=None, **kwargs):
        super().__init__(master, **kwargs)
        self.theme = theme_service
        self.config(
            bg=self.theme.colores.get("accento", "#e94560") if not kwargs.get('bg') else kwargs.get('bg'),
            fg=self.theme.colores.get("texto", "#ffffff") if not kwargs.get('fg') else kwargs.get('fg'),
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            bd=0,
            padx=20,
            pady=10,
            cursor="hand2"
        )
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        current_bg = self.cget('bg')
        self.config(bg=lighten_color(current_bg))

    def on_leave(self, e):
        self.config(bg=self.original_bg if hasattr(self, 'original_bg') else self.theme.colores.get("accento", "#e94560"))

class ModernEntry(tk.Entry):
    def __init__(self, master=None, theme_service=None, **kwargs):
        super().__init__(master, **kwargs)
        self.theme = theme_service
        self.config(
            bg=self.theme.colores.get("superficie3", "#2d3047"),
            fg=self.theme.colores.get("texto", "#ffffff"),
            insertbackground=self.theme.colores.get("texto", "#ffffff"),
            relief="flat",
            bd=2,
            highlightbackground=self.theme.colores.get("texto_secundario", "#b0b0b0"),
            highlightcolor=self.theme.colores.get("accento", "#e94560"),
            highlightthickness=1,
            font=("Segoe UI", 10)
        )

class ModernCombobox(ttk.Combobox):
    def __init__(self, master=None, theme_service=None, **kwargs):
        super().__init__(master, **kwargs)
        self.theme = theme_service
        self.config(font=("Segoe UI", 10))
        self._actualizar_estilo()
    
    def _actualizar_estilo(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TCombobox",
                        fieldbackground=self.theme.colores.get("superficie3", "#2d3047"),
                        background=self.theme.colores.get("superficie3", "#2d3047"),
                        foreground=self.theme.colores.get("texto", "#ffffff"),
                        borderwidth=0,
                        relief="flat")
        style.map('TCombobox',
                  fieldbackground=[('readonly', self.theme.colores.get("superficie3", "#2d3047"))],
                  selectbackground=[('readonly', self.theme.colores.get("accento", "#e94560"))],
                  selectforeground=[('readonly', self.theme.colores.get("texto", "#ffffff"))])