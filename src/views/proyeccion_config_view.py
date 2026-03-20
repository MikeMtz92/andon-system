# src/views/proyeccion_config_view.py

import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
from tkcalendar import DateEntry
from src.utils.helpers import is_light_color
from src.views.proyeccion_view import ProyeccionView
import logging

logger = logging.getLogger(__name__)

class ProyeccionConfigView:
    """Ventana de configuración de proyección"""
    
    def __init__(self, parent, controller, theme_service, falla_controller):
        self.parent = parent
        self.controller = controller
        self.theme = theme_service
        self.falla_controller = falla_controller
        
        self.config = controller.config_proyeccion
        self.config_contador = controller.falla_controller.config_contador
        
        self.ventana = tk.Toplevel(parent)
        self.ventana.title("Configurar Proyección")
        self.ventana.geometry("600x700")
        self.ventana.configure(bg=self.theme.colores["fondo"])
        self.ventana.resizable(True, True)
        self.ventana.transient(parent)
        self.ventana.grab_set()
        
        # Centrar
        self.ventana.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (600 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (700 // 2)
        self.ventana.geometry(f"600x700+{x}+{y}")
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Configura la interfaz de usuario"""
        main_frame = tk.Frame(self.ventana, bg=self.theme.colores["fondo"])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(main_frame,
                text="📺 Configurar Vista de Proyección",
                bg=self.theme.colores["fondo"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 16, "bold")).pack(pady=(0, 20))
        
        # Canvas con scroll
        canvas_frame = tk.Frame(main_frame, bg=self.theme.colores["fondo"])
        canvas_frame.pack(fill="both", expand=True)
        
        canvas = tk.Canvas(canvas_frame, bg=self.theme.colores["fondo"], highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.theme.colores["fondo"])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # ===== COLORES =====
        self._crear_seccion_colores(scrollable_frame)
        
        # ===== VISUALIZACIÓN =====
        self._crear_seccion_visualizacion(scrollable_frame)
        
        # ===== CONTADOR =====
        self._crear_seccion_contador(scrollable_frame)
        
        # ===== MODO DE VISUALIZACIÓN =====
        self._crear_seccion_modo(scrollable_frame)
        
        # ===== MONITOR =====
        self._crear_seccion_monitor(scrollable_frame)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # ===== BOTONES =====
        button_frame = tk.Frame(main_frame, bg=self.theme.colores["fondo"])
        button_frame.pack(fill="x", pady=(20, 0))
        
        tk.Button(button_frame,
                 text="🚫 Cancelar",
                 bg=self.theme.colores["danger"],
                 fg=self.theme.colores["texto"],
                 font=("Segoe UI", 11),
                 relief="flat",
                 padx=20,
                 pady=10,
                 cursor="hand2",
                 command=self.ventana.destroy).pack(side="left", padx=5)
        
        tk.Button(button_frame,
                 text="✅ Abrir Proyección",
                 bg=self.theme.colores["success"],
                 fg=self.theme.colores["texto"],
                 font=("Segoe UI", 11, "bold"),
                 relief="flat",
                 padx=20,
                 pady=10,
                 cursor="hand2",
                 command=self._abrir_proyeccion).pack(side="right", padx=5)
    
    def _crear_seccion_colores(self, parent):
        """Crea la sección de colores"""
        card = tk.Frame(parent, bg=self.theme.colores["card"], relief="flat", bd=1)
        card.pack(fill="x", pady=(0, 15))
        
        tk.Label(card,
                text="🎨 Personalización de Colores",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15, pady=(15, 10))
        
        # Fondo
        self._crear_selector_color(card, "Color de Fondo:", "color_fondo", self.config.get("color_fondo", "#000000"))
        
        # Texto
        self._crear_selector_color(card, "Color de Texto:", "color_texto", self.config.get("color_texto", "#FFFFFF"))
        
        # Acento
        self._crear_selector_color(card, "Color de Acento:", "color_acento", self.config.get("color_acento", "#e94560"))
        
        # Éxito
        self._crear_selector_color(card, "Color de Éxito:", "color_exito", self.config.get("color_exito", "#4CAF50"))
    
    def _crear_selector_color(self, parent, label, key, default):
        """Crea un selector de color"""
        frame = tk.Frame(parent, bg=self.theme.colores["card"])
        frame.pack(fill="x", padx=15, pady=5)
        
        tk.Label(frame,
                text=label,
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 10),
                width=20,
                anchor="w").pack(side="left")
        
        var = tk.StringVar(value=default)
        preview = tk.Frame(frame, bg=default, width=50, height=25)
        preview.pack(side="left", padx=5)
        preview.pack_propagate(False)
        
        tk.Button(frame,
                 text="Cambiar",
                 bg=self.theme.colores["card"],
                 fg=self.theme.colores["texto"],
                 font=("Segoe UI", 8),
                 relief="flat",
                 padx=10,
                 pady=2,
                 cursor="hand2",
                 command=lambda: self._cambiar_color(var, preview)).pack(side="left", padx=5)
        
        setattr(self, f"proy_{key}_var", var)
        setattr(self, f"proy_{key}_preview", preview)
    
    def _cambiar_color(self, var, preview):
        """Cambia un color"""
        color = colorchooser.askcolor(initialcolor=var.get())
        if color and color[1]:
            var.set(color[1])
            preview.config(bg=color[1])
    
    def _crear_seccion_visualizacion(self, parent):
        """Crea la sección de opciones de visualización"""
        card = tk.Frame(parent, bg=self.theme.colores["card"], relief="flat", bd=1)
        card.pack(fill="x", pady=(0, 15))
        
        tk.Label(card,
                text="👁️ Opciones de Visualización",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15, pady=(15, 10))
        
        self.mostrar_contador_var = tk.BooleanVar(value=self.config.get("mostrar_contador", True))
        tk.Checkbutton(card,
                    text="Mostrar contador de fallas activas",
                    variable=self.mostrar_contador_var,
                    bg=self.theme.colores["card"],
                    fg=self.theme.colores["texto"],
                    selectcolor=self.theme.colores["accento"],
                    font=("Segoe UI", 10)).pack(anchor="w", padx=15, pady=5)
        
        self.mostrar_pendientes_var = tk.BooleanVar(value=self.config.get("mostrar_pendientes", True))
        tk.Checkbutton(card,
                    text="Mostrar fallas pendientes en la tabla",
                    variable=self.mostrar_pendientes_var,
                    bg=self.theme.colores["card"],
                    fg=self.theme.colores["texto"],
                    selectcolor=self.theme.colores["accento"],
                    font=("Segoe UI", 10)).pack(anchor="w", padx=15, pady=5)
    
    def _crear_seccion_contador(self, parent):
        """Crea la sección del contador"""
        card = tk.Frame(parent, bg=self.theme.colores["card"], relief="flat", bd=1)
        card.pack(fill="x", pady=(0, 15))
        
        tk.Label(card,
                text="🔢 Configuración del Contador de Fallas",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15, pady=(15, 10))
        
        periodo_frame = tk.Frame(card, bg=self.theme.colores["card"])
        periodo_frame.pack(fill="x", padx=15, pady=5)
        
        tk.Label(periodo_frame,
                text="Reiniciar contador cada:",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 10)).pack(anchor="w")
        
        self.periodo_reset_var = tk.StringVar(value=self.config_contador.get("periodo_reset", "diario"))
        periodos = [
            ("12 horas", "horas_12"),
            ("Diario", "diario"),
            ("Semanal", "semanal"),
            ("Mensual", "mensual"),
            ("Anual", "anual"),
            ("Nunca", "nunca")
        ]
        
        for texto, valor in periodos:
            rb = tk.Radiobutton(periodo_frame,
                        text=texto,
                        variable=self.periodo_reset_var,
                        value=valor,
                        bg=self.theme.colores["card"],
                        fg=self.theme.colores["texto"],
                        selectcolor=self.theme.colores["accento"],
                        font=("Segoe UI", 9))
            rb.pack(anchor="w", padx=20, pady=2)
        
        # Info del contador actual
        info_frame = tk.Frame(card, bg=self.theme.colores["card"])
        info_frame.pack(fill="x", padx=15, pady=10)
        
        ultimo_reset = self.config_contador.get("ultimo_reset", "")
        tk.Label(info_frame,
                text=f"Último reset: {ultimo_reset[:16] if ultimo_reset else 'N/A'}",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto_secundario"],
                font=("Segoe UI", 9)).pack(anchor="w")
        
        tk.Label(info_frame,
                text=f"Número actual: {self.config_contador.get('consecutivo_actual', 0)}",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["success"],
                font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=2)
    
    def _crear_seccion_modo(self, parent):
        """Crea la sección de modo de visualización"""
        card = tk.Frame(parent, bg=self.theme.colores["card"], relief="flat", bd=1)
        card.pack(fill="x", pady=(0, 15))
        
        tk.Label(card,
                text="🖥️ Modo de Visualización",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15, pady=(15, 10))
        
        self.modo_var = tk.StringVar(value="ventana" if not self.config.get("pantalla_completa") else "completa")
        
        tk.Radiobutton(card,
                    text="🖥️ Ventana Movible",
                    variable=self.modo_var,
                    value="ventana",
                    bg=self.theme.colores["card"],
                    fg=self.theme.colores["texto"],
                    selectcolor=self.theme.colores["accento"],
                    font=("Segoe UI", 10)).pack(anchor="w", padx=15, pady=5)
        
        tk.Radiobutton(card,
                    text="📺 Pantalla Completa",
                    variable=self.modo_var,
                    value="completa",
                    bg=self.theme.colores["card"],
                    fg=self.theme.colores["texto"],
                    selectcolor=self.theme.colores["accento"],
                    font=("Segoe UI", 10)).pack(anchor="w", padx=15, pady=5)
        
        # Opciones de tamaño (solo para modo ventana)
        self.tamano_frame = tk.Frame(card, bg=self.theme.colores["card"])
        self.tamano_frame.pack(fill="x", padx=15, pady=10)
        
        tk.Label(self.tamano_frame,
                text="Tamaño y Posición:",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 10))
        
        dim_frame = tk.Frame(self.tamano_frame, bg=self.theme.colores["card"])
        dim_frame.pack(fill="x", pady=5)
        
        tk.Label(dim_frame,
                text="Ancho:",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto_secundario"],
                font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))
        
        self.ancho_var = tk.StringVar(value=str(self.config.get("ancho", 800)))
        tk.Entry(dim_frame,
                textvariable=self.ancho_var,
                width=8,
                bg=self.theme.colores.get("superficie3", "#2d3047"),
                fg=self.theme.colores["texto"],
                relief="flat",
                font=("Segoe UI", 10)).pack(side="left", padx=(0, 20))
        
        tk.Label(dim_frame,
                text="Alto:",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto_secundario"],
                font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))
        
        self.alto_var = tk.StringVar(value=str(self.config.get("alto", 600)))
        tk.Entry(dim_frame,
                textvariable=self.alto_var,
                width=8,
                bg=self.theme.colores.get("superficie3", "#2d3047"),
                fg=self.theme.colores["texto"],
                relief="flat",
                font=("Segoe UI", 10)).pack(side="left")
        
        pos_frame = tk.Frame(self.tamano_frame, bg=self.theme.colores["card"])
        pos_frame.pack(fill="x", pady=5)
        
        tk.Label(pos_frame,
                text="Posición X:",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto_secundario"],
                font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))
        
        self.x_var = tk.StringVar(value=str(self.config.get("x", 100)))
        tk.Entry(pos_frame,
                textvariable=self.x_var,
                width=8,
                bg=self.theme.colores.get("superficie3", "#2d3047"),
                fg=self.theme.colores["texto"],
                relief="flat",
                font=("Segoe UI", 10)).pack(side="left", padx=(0, 20))
        
        tk.Label(pos_frame,
                text="Posición Y:",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto_secundario"],
                font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))
        
        self.y_var = tk.StringVar(value=str(self.config.get("y", 100)))
        tk.Entry(pos_frame,
                textvariable=self.y_var,
                width=8,
                bg=self.theme.colores.get("superficie3", "#2d3047"),
                fg=self.theme.colores["texto"],
                relief="flat",
                font=("Segoe UI", 10)).pack(side="left")
    
    def _crear_seccion_monitor(self, parent):
        """Crea la sección de monitor"""
        card = tk.Frame(parent, bg=self.theme.colores["card"], relief="flat", bd=1)
        card.pack(fill="x", pady=(0, 15))
        
        tk.Label(card,
                text="🖥️ Seleccionar Monitor",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15, pady=(15, 10))
        
        self.monitor_frame = tk.Frame(card, bg=self.theme.colores["card"])
        self.monitor_frame.pack(fill="x", padx=15, pady=5)
        
        self.monitor_var = tk.IntVar(value=self.config.get("monitor", 0))
        
        # Detectar monitores
        self._detectar_monitores()
        
        self.recordar_var = tk.BooleanVar(value=self.config.get("recordar_posicion", True))
        tk.Checkbutton(card,
                    text="💾 Recordar posición y tamaño",
                    variable=self.recordar_var,
                    bg=self.theme.colores["card"],
                    fg=self.theme.colores["texto"],
                    selectcolor=self.theme.colores["accento"],
                    font=("Segoe UI", 10)).pack(anchor="w", padx=15, pady=10)
    
    def _detectar_monitores(self):
        """Detecta monitores disponibles"""
        for widget in self.monitor_frame.winfo_children():
            widget.destroy()
        
        try:
            from screeninfo import get_monitors
            monitores = get_monitors()
            for i, monitor in enumerate(monitores):
                frame = tk.Frame(self.monitor_frame, bg=self.theme.colores["card"])
                frame.pack(fill="x", pady=2)
                
                rb = tk.Radiobutton(frame,
                                   text=f"Monitor {i+1}: {monitor.width}x{monitor.height}",
                                   variable=self.monitor_var,
                                   value=i,
                                   bg=self.theme.colores["card"],
                                   fg=self.theme.colores["texto"],
                                   selectcolor=self.theme.colores["accento"],
                                   font=("Segoe UI", 9))
                rb.pack(anchor="w", padx=10)
                
                if i == self.config.get("monitor", 0):
                    rb.select()
        except:
            # Fallback a monitor único
            frame = tk.Frame(self.monitor_frame, bg=self.theme.colores["card"])
            frame.pack(fill="x", pady=2)
            rb = tk.Radiobutton(frame,
                               text="Monitor Principal",
                               variable=self.monitor_var,
                               value=0,
                               bg=self.theme.colores["card"],
                               fg=self.theme.colores["texto"],
                               selectcolor=self.theme.colores["accento"],
                               font=("Segoe UI", 9))
            rb.pack(anchor="w", padx=10)
            rb.select()
    
    def _abrir_proyeccion(self):
        """Guarda configuración y abre proyección"""
        # Guardar configuración
        self.config.update({
            "color_fondo": getattr(self, "proy_color_fondo_var", tk.StringVar(value="#000000")).get(),
            "color_texto": getattr(self, "proy_color_texto_var", tk.StringVar(value="#FFFFFF")).get(),
            "color_acento": getattr(self, "proy_color_acento_var", tk.StringVar(value="#e94560")).get(),
            "color_exito": getattr(self, "proy_color_exito_var", tk.StringVar(value="#4CAF50")).get(),
            "mostrar_contador": self.mostrar_contador_var.get(),
            "mostrar_pendientes": self.mostrar_pendientes_var.get(),
            "pantalla_completa": (self.modo_var.get() == "completa"),
            "recordar_posicion": self.recordar_var.get(),
            "monitor": self.monitor_var.get()
        })
        
        if self.modo_var.get() == "ventana":
            try:
                self.config["ancho"] = int(self.ancho_var.get())
                self.config["alto"] = int(self.alto_var.get())
                self.config["x"] = int(self.x_var.get())
                self.config["y"] = int(self.y_var.get())
            except ValueError:
                messagebox.showerror("Error", "Ingresa valores numéricos válidos")
                return
        
        # Guardar configuración del contador
        self.config_contador["periodo_reset"] = self.periodo_reset_var.get()
        self.controller.config_model.guardar_config_contador(self.config_contador)
        
        # Guardar configuración de proyección
        self.controller.config_model.guardar_config_proyeccion(self.config)
        
        # Cerrar esta ventana
        self.ventana.destroy()
        
        # Abrir proyección
        ProyeccionView(self.parent, self.controller, self.theme, self.falla_controller)