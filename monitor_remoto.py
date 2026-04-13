# monitor_remoto.py
"""
Sistema Andon - Monitor Remoto
Cliente ligero para visualizar fallas activas en tiempo real desde otra PC.
Se conecta a la misma base de datos MySQL que el sistema principal.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import mysql.connector
import threading
import time
import os
import sys
import json
from typing import List, Dict
import pygame  # Para reproducir MP3
import hashlib
from colorsys import hsv_to_rgb

# Configurar logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def solo_hora(fecha_completa):
    """Extrae solo la hora de una fecha completa"""
    if not fecha_completa:
        return ""
    try:
        if len(fecha_completa) <= 8 and ":" in fecha_completa:
            return fecha_completa
        return datetime.strptime(str(fecha_completa), "%Y-%m-%d %H:%M:%S").strftime("%H:%M:%S")
    except:
        return str(fecha_completa) if fecha_completa else ""


def is_light_color(hex_color):
    """Determina si un color es claro"""
    if hex_color.startswith('#'):
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    else:
        rgb = hex_color
    luminance = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255
    return luminance > 0.5


class MonitorRemoto:
    """Cliente remoto para monitoreo de fallas Andon"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Andon Remote Monitor - Sistema de Monitoreo de Fallas")
        
        # Configuración inicial
        self.db_config = None
        self.connection = None
        self.cursor = None
        self.running = True
        self.fallas_activas: List[Dict] = []
        self.fallas_previas: List[Dict] = []  # Para detectar nuevas fallas
        self.tipos_colores: Dict[str, str] = {}
        self.tipos_disponibles: List[str] = []
        self.maquinas_disponibles: List[str] = []
        
        # Configuración de sonidos
        pygame.mixer.init()
        self.sonidos_configurados: Dict[str, str] = {}  # tipo_falla -> ruta_archivo
        self.sonidos_habilitados = tk.BooleanVar(value=True)
        
        # Variables de UI
        self.color_fondo = "#000000"
        self.color_texto = "#FFFFFF"
        
        # Tamaño de fuente (valor base)
        self.font_size = tk.IntVar(value=12)  # Tamaño base para la tabla
        
        # Configuración de conexión
        self.host_var = tk.StringVar(value="localhost")
        self.port_var = tk.StringVar(value="3306")
        self.user_var = tk.StringVar(value="root")
        self.password_var = tk.StringVar(value="")
        self.database_var = tk.StringVar(value="andon_db")
        
        # Filtros
        self.filtro_maquina_var = tk.StringVar(value="TODAS")
        self.filtro_tipo_var = tk.StringVar(value="TODOS")
        
        # Estado de conexión
        self.connected = False
        self.lock = threading.Lock()
        
        self._setup_ui()
        self._cargar_configuracion()
        self._cargar_configuracion_sonidos()
        self._cargar_configuracion_fuente()
        
        # Iniciar actualización automática
        self._iniciar_actualizacion()
        
        self.root.mainloop()
    
    def _setup_ui(self):
        """Configura la interfaz de usuario"""
        self.root.configure(bg=self.color_fondo)
        self.root.geometry("1400x800")
        self.root.minsize(1000, 600)
        
        # Configurar para pantalla completa opcional
        self.root.bind('<F11>', lambda e: self._toggle_fullscreen())
        self.root.bind('<Escape>', lambda e: self._salir_fullscreen())
        
        # ===== HEADER =====
        header_frame = tk.Frame(self.root, bg="#1a1a2e")
        header_frame.pack(fill="x", padx=0, pady=0)
        
        # Título
        title_label = tk.Label(
            header_frame,
            text="🔴 ANDON REMOTE MONITOR",
            bg="#1a1a2e",
            fg="#e94560",
            font=("Segoe UI", 24, "bold")
        )
        title_label.pack(side="left", padx=20, pady=15)
        
        # Panel de estado
        status_frame = tk.Frame(header_frame, bg="#1a1a2e")
        status_frame.pack(side="right", padx=20, pady=15)
        
        self.status_indicator = tk.Label(
            status_frame,
            text="●",
            fg="#FF5252",
            bg="#1a1a2e",
            font=("Arial", 14)
        )
        self.status_indicator.pack(side="left", padx=(0, 5))
        
        self.status_label = tk.Label(
            status_frame,
            text="Desconectado",
            bg="#1a1a2e",
            fg="#b0b0b0",
            font=("Segoe UI", 10)
        )
        self.status_label.pack(side="left", padx=(0, 10))
        
        # Botón configurar
        self.config_btn = tk.Button(
            status_frame,
            text="⚙️ Configurar Conexión",
            bg="#2196F3",
            fg="white",
            font=("Segoe UI", 9),
            relief="flat",
            padx=10,
            pady=5,
            cursor="hand2",
            command=self._mostrar_configuracion
        )
        self.config_btn.pack(side="left", padx=2)
        
        # Botón configurar sonidos
        self.sound_btn = tk.Button(
            status_frame,
            text="🔊 Configurar Sonidos",
            bg="#9C27B0",
            fg="white",
            font=("Segoe UI", 9),
            relief="flat",
            padx=10,
            pady=5,
            cursor="hand2",
            command=self._mostrar_configuracion_sonidos
        )
        self.sound_btn.pack(side="left", padx=2)
        
        # Botón configurar fuente
        self.font_btn = tk.Button(
            status_frame,
            text="🔤 Tamaño Letra",
            bg="#FF9800",
            fg="white",
            font=("Segoe UI", 9),
            relief="flat",
            padx=10,
            pady=5,
            cursor="hand2",
            command=self._mostrar_configuracion_fuente
        )
        self.font_btn.pack(side="left", padx=2)
        
        # ===== BARRA DE FILTROS =====
        filters_frame = tk.Frame(self.root, bg=self.color_fondo)
        filters_frame.pack(fill="x", padx=20, pady=10)
        
        # Filtro por máquina
        tk.Label(
            filters_frame,
            text="🔍 Máquina:",
            bg=self.color_fondo,
            fg=self.color_texto,
            font=("Segoe UI", 11, "bold")
        ).pack(side="left", padx=(0, 10))
        
        self.filtro_maquina_combo = ttk.Combobox(
            filters_frame,
            textvariable=self.filtro_maquina_var,
            values=["TODAS"],
            width=10,
            state="readonly",
            font=("Segoe UI", 10)
        )
        self.filtro_maquina_combo.pack(side="left", padx=(0, 20))
        
        # Filtro por tipo de falla
        tk.Label(
            filters_frame,
            text="Tipo de falla:",
            bg=self.color_fondo,
            fg=self.color_texto,
            font=("Segoe UI", 11, "bold")
        ).pack(side="left", padx=(0, 10))
        
        self.filtro_tipo_combo = ttk.Combobox(
            filters_frame,
            textvariable=self.filtro_tipo_var,
            values=["TODOS"],
            width=20,
            state="readonly",
            font=("Segoe UI", 10)
        )
        self.filtro_tipo_combo.pack(side="left", padx=(0, 20))
        
        # Botón actualizar
        self.refresh_btn = tk.Button(
            filters_frame,
            text="🔄 Actualizar listas",
            bg="#2196F3",
            fg="white",
            font=("Segoe UI", 9),
            relief="flat",
            padx=10,
            pady=3,
            cursor="hand2",
            command=self._actualizar_listas_completas
        )
        self.refresh_btn.pack(side="left")
        
        # Checkbox habilitar sonidos
        self.sound_check = tk.Checkbutton(
            filters_frame,
            text="🔊 Sonidos",
            variable=self.sonidos_habilitados,
            bg=self.color_fondo,
            fg=self.color_texto,
            selectcolor=self.color_fondo,
            font=("Segoe UI", 10),
            cursor="hand2"
        )
        self.sound_check.pack(side="left", padx=(20, 0))
        
        # Indicador de filtros activos
        self.filtro_label = tk.Label(
            filters_frame,
            text="",
            bg=self.color_fondo,
            fg="#FFC107",
            font=("Segoe UI", 10, "italic")
        )
        self.filtro_label.pack(side="left", padx=(20, 0))
        
        # ===== CONTADOR DE FALLAS =====
        counter_frame = tk.Frame(self.root, bg=self.color_fondo)
        counter_frame.pack(fill="x", padx=20, pady=10)
        
        self.counter_label = tk.Label(
            counter_frame,
            text="0 fallas activas",
            bg=self.color_fondo,
            fg="#FF5252",
            font=("Segoe UI", 18, "bold")
        )
        self.counter_label.pack(side="left")
        
        # Hora y fecha
        time_frame = tk.Frame(counter_frame, bg=self.color_fondo)
        time_frame.pack(side="right")
        
        self.clock_label = tk.Label(
            time_frame,
            text=datetime.now().strftime("%H:%M:%S"),
            bg=self.color_fondo,
            fg="#4CAF50",
            font=("Segoe UI", 18, "bold")
        )
        self.clock_label.pack(side="left", padx=5)
        
        self.date_label = tk.Label(
            time_frame,
            text=datetime.now().strftime("%d/%m/%Y"),
            bg=self.color_fondo,
            fg=self.color_texto,
            font=("Segoe UI", 18)
        )
        self.date_label.pack(side="left", padx=5)
        
        # ===== TABLA DE FALLAS =====
        self.table_frame = tk.Frame(self.root, bg=self.color_fondo)
        self.table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self._crear_tabla()
        
        # ===== FOOTER =====
        footer_frame = tk.Frame(self.root, bg="#1a1a2e", height=30)
        footer_frame.pack(fill="x", side="bottom")
        footer_frame.pack_propagate(False)
        
        tk.Label(
            footer_frame,
            text="Andon Remote Monitor - Conectado a MySQL | F11 = Pantalla completa | Filtros: Máquina y Tipo de Falla | 🔊 Sonidos personalizables por tipo de falla | 🔤 Ajusta el tamaño de letra",
            bg="#1a1a2e",
            fg="#b0b0b0",
            font=("Segoe UI", 9)
        ).pack(pady=5)
        
        # Actualizar reloj
        self._actualizar_reloj()
        
        # Vincular eventos de cambio de filtro
        self.filtro_maquina_var.trace_add("write", lambda *args: self._aplicar_filtros())
        self.filtro_tipo_var.trace_add("write", lambda *args: self._aplicar_filtros())
    
    def _crear_tabla(self):
        """Crea la tabla de fallas igual que la pantalla de proyección"""
        for widget in self.table_frame.winfo_children():
            widget.destroy()
        
        # Configurar estilo
        style = ttk.Style()
        style.theme_use('clam')
        
        # Usar el tamaño de fuente actual
        current_font_size = self.font_size.get()
        style.configure("Monitor.Treeview",
                       background=self.color_fondo,
                       foreground=self.color_texto,
                       rowheight=current_font_size + 33,  # Altura dinámica
                       fieldbackground=self.color_fondo,
                       borderwidth=0,
                       font=("Segoe UI", current_font_size))
        style.configure("Monitor.Treeview.Heading",
                       background="#2d3047",
                       foreground=self.color_texto,
                       relief="flat",
                       borderwidth=0,
                       font=("Segoe UI", current_font_size + 1, "bold"))
        
        # Columnas igual que la pantalla de proyección
        columnas = ("#", "Máquina", "Tipo", "Inicio", "Proceso", "Fin", "Estado")
        self.tree = ttk.Treeview(
            self.table_frame,
            columns=columnas,
            show="headings",
            style="Monitor.Treeview"
        )
        
        # Configurar columnas con anchos dinámicos basados en tamaño de fuente
        base_widths = [80, 100, 200, 120, 120, 120, 120]
        factor = max(0.8, min(1.5, current_font_size / 12))
        anchos = [int(w * factor) for w in base_widths]
        
        for col, ancho in zip(columnas, anchos):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=ancho, anchor="center")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Diccionario para almacenar tags ya configurados
        self.configured_tags = set()
    
    def _actualizar_tamaño_fuente(self, nuevo_tamaño=None):
        """Actualiza el tamaño de fuente en toda la interfaz"""
        if nuevo_tamaño is not None:
            self.font_size.set(nuevo_tamaño)
        
        size = self.font_size.get()
        
        # Actualizar estilo de la tabla
        style = ttk.Style()
        style.configure("Monitor.Treeview",
                       font=("Segoe UI", size),
                       rowheight=size + 33)
        style.configure("Monitor.Treeview.Heading",
                       font=("Segoe UI", size + 1, "bold"))
        
        # Actualizar anchos de columnas
        if hasattr(self, 'tree') and self.tree.winfo_exists():
            base_widths = [80, 100, 200, 120, 120, 120, 120]
            factor = max(0.8, min(1.5, size / 12))
            anchos = [int(w * factor) for w in base_widths]
            for col, ancho in zip(("#", "Máquina", "Tipo", "Inicio", "Proceso", "Fin", "Estado"), anchos):
                self.tree.column(col, width=ancho)
        
        # Actualizar contador
        if hasattr(self, 'counter_label') and self.counter_label.winfo_exists():
            self.counter_label.config(font=("Segoe UI", int(size * 1.5), "bold"))
        
        # Actualizar reloj
        if hasattr(self, 'clock_label') and self.clock_label.winfo_exists():
            self.clock_label.config(font=("Segoe UI", int(size * 1.5), "bold"))
            self.date_label.config(font=("Segoe UI", int(size * 1.5)))
        
        # Actualizar filtros label
        if hasattr(self, 'filtro_label') and self.filtro_label.winfo_exists():
            self.filtro_label.config(font=("Segoe UI", size - 2, "italic"))
        
        # Guardar configuración
        self._guardar_configuracion_fuente()
        
        # Refrescar la tabla para aplicar nuevos tamaños a los tags
        self._aplicar_filtros()
    
    def _cargar_configuracion_fuente(self):
        """Carga la configuración del tamaño de fuente"""
        font_config_file = "monitor_font_config.json"
        if os.path.exists(font_config_file):
            try:
                with open(font_config_file, 'r') as f:
                    config = json.load(f)
                    tamaño = config.get("font_size", 12)
                    # Limitar entre 8 y 30
                    tamaño = max(8, min(30, tamaño))
                    self.font_size.set(tamaño)
                    self._actualizar_tamaño_fuente()
                    logger.info(f"Configuración de fuente cargada: tamaño {tamaño}")
            except Exception as e:
                logger.error(f"Error cargando configuración de fuente: {e}")
    
    def _guardar_configuracion_fuente(self):
        """Guarda la configuración del tamaño de fuente"""
        font_config_file = "monitor_font_config.json"
        try:
            config = {"font_size": self.font_size.get()}
            with open(font_config_file, 'w') as f:
                json.dump(config, f, indent=4)
            logger.info(f"Configuración de fuente guardada: tamaño {self.font_size.get()}")
        except Exception as e:
            logger.error(f"Error guardando configuración de fuente: {e}")
    
    def _mostrar_configuracion_fuente(self):
        """Muestra ventana para ajustar el tamaño de letra"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Configurar Tamaño de Letra")
        dialog.geometry("450x350")
        dialog.configure(bg="#1a1a2e")
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (450 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (350 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        tk.Label(
            dialog,
            text="🔤 Configurar Tamaño de Letra",
            bg="#1a1a2e",
            fg="white",
            font=("Segoe UI", 16, "bold")
        ).pack(pady=20)
        
        tk.Label(
            dialog,
            text="Ajusta el tamaño de la letra en la tabla y textos principales:",
            bg="#1a1a2e",
            fg="#b0b0b0",
            font=("Segoe UI", 10)
        ).pack()
        
        # Frame para el control deslizante
        slider_frame = tk.Frame(dialog, bg="#16213e", padx=20, pady=20)
        slider_frame.pack(fill="x", padx=30, pady=20)
        
        # Variable temporal para el tamaño
        temp_size = tk.IntVar(value=self.font_size.get())
        
        # Label de vista previa
        preview_label = tk.Label(
            slider_frame,
            text=f"Tamaño actual: {temp_size.get()}px\nEjemplo de texto",
            bg="#16213e",
            fg="white",
            font=("Segoe UI", temp_size.get()),
            pady=10
        )
        preview_label.pack(pady=10)
        
        # Slider para tamaño
        def on_slider_change(val):
            size = int(float(val))
            preview_label.config(
                text=f"Tamaño actual: {size}px\nEjemplo de texto",
                font=("Segoe UI", size)
            )
            temp_size.set(size)
        
        slider = tk.Scale(
            slider_frame,
            from_=8,
            to=30,
            orient="horizontal",
            length=300,
            bg="#16213e",
            fg="white",
            highlightbackground="#16213e",
            troughcolor="#0f3460",
            command=on_slider_change
        )
        slider.set(temp_size.get())  # Establecer el valor después de crear el slider
        slider.pack(pady=10)
        
        # Label con rangos
        range_frame = tk.Frame(slider_frame, bg="#16213e")
        range_frame.pack(fill="x")
        tk.Label(range_frame, text="Pequeño (8px)", bg="#16213e", fg="#888").pack(side="left")
        tk.Label(range_frame, text="Grande (30px)", bg="#16213e", fg="#888").pack(side="right")
        
        # Botones
        btn_frame = tk.Frame(dialog, bg="#1a1a2e")
        btn_frame.pack(pady=20)
        
        def aplicar_y_cerrar():
            self.font_size.set(temp_size.get())
            self._actualizar_tamaño_fuente()
            dialog.destroy()
            messagebox.showinfo("Configuración Guardada", f"Tamaño de letra ajustado a {self.font_size.get()}px", parent=self.root)
        
        tk.Button(
            btn_frame,
            text="✅ Aplicar y Cerrar",
            command=aplicar_y_cerrar,
            bg="#4CAF50",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2"
        ).pack(side="left", padx=5)
        
        tk.Button(
            btn_frame,
            text="❌ Cancelar",
            command=dialog.destroy,
            bg="#FF5252",
            fg="white",
            font=("Segoe UI", 11),
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2"
        ).pack(side="left", padx=5)
        
        # Botón para resetear a valor por defecto
        def resetear():
            slider.set(12)
            on_slider_change(12)
        
        tk.Button(
            btn_frame,
            text="🔄 Resetear (12px)",
            command=resetear,
            bg="#2196F3",
            fg="white",
            font=("Segoe UI", 10),
            relief="flat",
            padx=15,
            pady=5,
            cursor="hand2"
        ).pack(side="left", padx=5)
    
    def _actualizar_reloj(self):
        """Actualiza el reloj en tiempo real"""
        if hasattr(self, 'clock_label') and self.clock_label.winfo_exists():
            ahora = datetime.now()
            self.clock_label.config(text=ahora.strftime("%H:%M:%S"))
            self.date_label.config(text=ahora.strftime("%d/%m/%Y"))
            self.root.after(1000, self._actualizar_reloj)
    
    def _cargar_configuracion(self):
        """Carga configuración de conexión desde archivo"""
        config_file = "monitor_config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    self.host_var.set(config.get("host", "localhost"))
                    self.port_var.set(str(config.get("port", 3306)))
                    self.user_var.set(config.get("user", "root"))
                    self.password_var.set(config.get("password", ""))
                    self.database_var.set(config.get("database", "andon_db"))
                    logger.info("Configuración cargada desde archivo")
                    self._conectar()
            except Exception as e:
                logger.error(f"Error cargando configuración: {e}")
    
    def _guardar_configuracion(self):
        """Guarda configuración de conexión"""
        config_file = "monitor_config.json"
        try:
            config = {
                "host": self.host_var.get(),
                "port": int(self.port_var.get()),
                "user": self.user_var.get(),
                "password": self.password_var.get(),
                "database": self.database_var.get()
            }
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=4)
            logger.info("Configuración guardada")
        except Exception as e:
            logger.error(f"Error guardando configuración: {e}")
    
    def _cargar_configuracion_sonidos(self):
        """Carga la configuración de sonidos desde archivo local"""
        sound_config_file = "monitor_sounds.json"
        if os.path.exists(sound_config_file):
            try:
                with open(sound_config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.sonidos_configurados = config.get("sonidos", {})
                    self.sonidos_habilitados.set(config.get("habilitados", True))
                    logger.info(f"Configuración de sonidos cargada: {len(self.sonidos_configurados)} sonidos")
            except Exception as e:
                logger.error(f"Error cargando configuración de sonidos: {e}")
    
    def _guardar_configuracion_sonidos(self):
        """Guarda la configuración de sonidos en archivo local"""
        sound_config_file = "monitor_sounds.json"
        try:
            config = {
                "sonidos": self.sonidos_configurados,
                "habilitados": self.sonidos_habilitados.get()
            }
            with open(sound_config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            logger.info("Configuración de sonidos guardada")
        except Exception as e:
            logger.error(f"Error guardando configuración de sonidos: {e}")
    
    def _mostrar_configuracion_sonidos(self):
        """Muestra ventana para configurar sonidos por tipo de falla"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Configurar Sonidos por Tipo de Falla")
        dialog.geometry("650x550")
        dialog.configure(bg="#1a1a2e")
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (650 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (550 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        tk.Label(
            dialog,
            text="🔊 Configurar Sonidos por Tipo de Falla",
            bg="#1a1a2e",
            fg="white",
            font=("Segoe UI", 16, "bold")
        ).pack(pady=20)
        
        tk.Label(
            dialog,
            text="Asigna un archivo MP3 a cada tipo de falla. Cuando ocurra una falla,\nse reproducirá el sonido correspondiente.",
            bg="#1a1a2e",
            fg="#b0b0b0",
            font=("Segoe UI", 10),
            justify="center"
        ).pack(pady=(0, 20))
        
        # Frame con scroll para los tipos de falla
        canvas_frame = tk.Frame(dialog, bg="#1a1a2e")
        canvas_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        canvas = tk.Canvas(canvas_frame, bg="#1a1a2e", highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#1a1a2e")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Obtener tipos de falla disponibles
        tipos = [t for t in self.tipos_disponibles if t != "TODOS"]
        if not tipos:
            # Si no hay tipos cargados, usar los de la BD
            try:
                if self.connection and self.cursor:
                    self.cursor.execute("SELECT nombre FROM tipos_falla ORDER BY orden")
                    tipos = [t["nombre"] for t in self.cursor.fetchall()]
            except:
                tipos = ["Mantenimiento", "Producción", "Calidad", "Materiales", "Ingeniería"]
        
        # Diccionario para almacenar las variables de ruta y labels
        rutas_vars = {}
        label_refs = {}
        
        for tipo in tipos:
            frame = tk.Frame(scrollable_frame, bg="#16213e", relief="flat", bd=1)
            frame.pack(fill="x", pady=5, padx=5)
            
            # Label del tipo
            tk.Label(
                frame,
                text=tipo,
                bg="#16213e",
                fg="white",
                font=("Segoe UI", 11, "bold"),
                width=20,
                anchor="w"
            ).pack(side="left", padx=10, pady=10)
            
            # Mostrar archivo actual
            ruta_actual = self.sonidos_configurados.get(tipo, "")
            nombre_archivo = os.path.basename(ruta_actual) if ruta_actual else "Sin asignar"
            
            ruta_label = tk.Label(
                frame,
                text=nombre_archivo[:40],
                bg="#0f3460",
                fg="#4CAF50" if ruta_actual else "#FFA500",
                font=("Segoe UI", 9),
                width=30,
                anchor="w",
                relief="flat"
            )
            ruta_label.pack(side="left", padx=10, fill="x", expand=True)
            
            # Guardar referencia
            label_refs[tipo] = ruta_label
            
            # Función para seleccionar archivo (usando closure correcto)
            def seleccionar_sonido(t=tipo, label=ruta_label):
                file_path = filedialog.askopenfilename(
                    title=f"Seleccionar sonido para {t}",
                    filetypes=[("Archivos MP3", "*.mp3"), ("Todos los archivos", "*.*")]
                )
                if file_path:
                    self.sonidos_configurados[t] = file_path
                    label.config(text=os.path.basename(file_path)[:40], fg="#4CAF50")
                    # Probar sonido
                    try:
                        pygame.mixer.music.load(file_path)
                        pygame.mixer.music.play()
                    except Exception as e:
                        logger.error(f"Error probando sonido: {e}")
            
            # Botón seleccionar
            tk.Button(
                frame,
                text="📁 Seleccionar",
                command=seleccionar_sonido,
                bg="#2196F3",
                fg="white",
                font=("Segoe UI", 9),
                relief="flat",
                padx=10,
                pady=5,
                cursor="hand2"
            ).pack(side="left", padx=5)
            
            # Función para probar sonido
            def probar_sonido(t=tipo):
                ruta = self.sonidos_configurados.get(t, "")
                if ruta and os.path.exists(ruta):
                    try:
                        pygame.mixer.music.load(ruta)
                        pygame.mixer.music.play()
                    except Exception as e:
                        messagebox.showerror("Error", f"No se pudo reproducir: {e}", parent=dialog)
                else:
                    messagebox.showwarning("Sin sonido", f"No hay sonido asignado para {t}", parent=dialog)
            
            # Botón probar
            tk.Button(
                frame,
                text="🔊 Probar",
                command=probar_sonido,
                bg="#4CAF50",
                fg="white",
                font=("Segoe UI", 9),
                relief="flat",
                padx=10,
                pady=5,
                cursor="hand2"
            ).pack(side="left", padx=5)
            
            # Función para eliminar sonido
            def eliminar_sonido(t=tipo, label=ruta_label):
                if t in self.sonidos_configurados:
                    del self.sonidos_configurados[t]
                    label.config(text="Sin asignar", fg="#FFA500")
            
            # Botón eliminar
            tk.Button(
                frame,
                text="❌ Eliminar",
                command=eliminar_sonido,
                bg="#FF5252",
                fg="white",
                font=("Segoe UI", 9),
                relief="flat",
                padx=10,
                pady=5,
                cursor="hand2"
            ).pack(side="left", padx=5)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Botones principales
        btn_frame = tk.Frame(dialog, bg="#1a1a2e")
        btn_frame.pack(fill="x", padx=20, pady=20)
        
        def guardar_y_cerrar():
            self._guardar_configuracion_sonidos()
            dialog.destroy()
            messagebox.showinfo("Configuración Guardada", "Los sonidos se han guardado correctamente.", parent=self.root)
        
        tk.Button(
            btn_frame,
            text="💾 Guardar y Cerrar",
            command=guardar_y_cerrar,
            bg="#4CAF50",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2"
        ).pack(side="right", padx=5)
        
        tk.Button(
            btn_frame,
            text="❌ Cancelar",
            command=dialog.destroy,
            bg="#FF5252",
            fg="white",
            font=("Segoe UI", 11),
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2"
        ).pack(side="right", padx=5)
        
        # Botón para silenciar todos
        def silenciar_todos():
            self.sonidos_configurados.clear()
            # Actualizar labels
            for tipo, label in label_refs.items():
                label.config(text="Sin asignar", fg="#FFA500")
        
        tk.Button(
            btn_frame,
            text="🔇 Silenciar Todos",
            command=silenciar_todos,
            bg="#FF9800",
            fg="white",
            font=("Segoe UI", 10),
            relief="flat",
            padx=15,
            pady=5,
            cursor="hand2"
        ).pack(side="left", padx=5)
    
    def _reproducir_sonido_para_tipo(self, tipo: str):
        """Reproduce el sonido configurado para un tipo de falla"""
        if not self.sonidos_habilitados.get():
            return
        
        ruta_sonido = self.sonidos_configurados.get(tipo)
        if ruta_sonido and os.path.exists(ruta_sonido):
            try:
                # Reproducir en un hilo separado para no bloquear la UI
                def play():
                    try:
                        pygame.mixer.music.load(ruta_sonido)
                        pygame.mixer.music.play()
                    except Exception as e:
                        logger.error(f"Error reproduciendo sonido: {e}")
                
                threading.Thread(target=play, daemon=True).start()
                logger.debug(f"Reproduciendo sonido para {tipo}: {ruta_sonido}")
            except Exception as e:
                logger.error(f"Error con sonido {tipo}: {e}")
        else:
            # Sonido genérico (beep) si no hay configurado
            if self.sonidos_habilitados.get():
                self._reproducir_beep()
    
    def _reproducir_beep(self):
        """Reproduce un beep genérico (usando winsound en Windows)"""
        try:
            import winsound
            threading.Thread(target=lambda: winsound.Beep(1500, 500), daemon=True).start()
        except:
            try:
                import sys
                if sys.platform == "linux":
                    # Para Linux, usar print('\a') o pygame
                    print('\a', end='', flush=True)
            except:
                pass
    
    def _mostrar_configuracion(self):
        """Muestra ventana de configuración de conexión"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Configurar Conexión MySQL")
        dialog.geometry("450x400")
        dialog.configure(bg="#1a1a2e")
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (450 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (400 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        tk.Label(
            dialog,
            text="🔌 Configuración de Conexión MySQL",
            bg="#1a1a2e",
            fg="white",
            font=("Segoe UI", 16, "bold")
        ).pack(pady=20)
        
        form_frame = tk.Frame(dialog, bg="#16213e")
        form_frame.pack(fill="both", expand=True, padx=30, pady=10)
        
        campos = [
            ("Host:", self.host_var),
            ("Puerto:", self.port_var),
            ("Usuario:", self.user_var),
            ("Contraseña:", self.password_var, True),
            ("Base de Datos:", self.database_var)
        ]
        
        for campo in campos:
            frame = tk.Frame(form_frame, bg="#16213e")
            frame.pack(fill="x", pady=5)
            
            tk.Label(
                frame,
                text=campo[0],
                bg="#16213e",
                fg="#b0b0b0",
                font=("Segoe UI", 10),
                width=15,
                anchor="w"
            ).pack(side="left")
            
            entry = tk.Entry(
                frame,
                textvariable=campo[1],
                width=25,
                bg="#0f3460",
                fg="white",
                relief="flat",
                font=("Segoe UI", 10)
            )
            if len(campo) > 2 and campo[2]:
                entry.config(show="•")
            entry.pack(side="left", padx=5)
        
        self.config_status = tk.Label(
            form_frame,
            text="",
            bg="#16213e",
            fg="#FFC107",
            font=("Segoe UI", 9)
        )
        self.config_status.pack(pady=10)
        
        btn_frame = tk.Frame(dialog, bg="#1a1a2e")
        btn_frame.pack(pady=20)
        
        def test_conexion():
            try:
                conn = mysql.connector.connect(
                    host=self.host_var.get(),
                    port=int(self.port_var.get()),
                    user=self.user_var.get(),
                    password=self.password_var.get(),
                    database=self.database_var.get(),
                    connection_timeout=10,
                    use_pure=True
                )
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchall()
                cursor.close()
                conn.close()
                self.config_status.config(text="✅ Conexión exitosa!", fg="#4CAF50")
            except Exception as e:
                self.config_status.config(text=f"❌ Error: {str(e)[:50]}", fg="#FF5252")
        
        def guardar():
            self._guardar_configuracion()
            dialog.destroy()
            self._conectar()
        
        tk.Button(
            btn_frame,
            text="🔌 Probar Conexión",
            command=test_conexion,
            bg="#2196F3",
            fg="white",
            font=("Segoe UI", 10),
            relief="flat",
            padx=15,
            pady=5,
            cursor="hand2"
        ).pack(side="left", padx=5)
        
        tk.Button(
            btn_frame,
            text="✅ Guardar y Conectar",
            command=guardar,
            bg="#4CAF50",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=15,
            pady=5,
            cursor="hand2"
        ).pack(side="left", padx=5)
        
        tk.Button(
            btn_frame,
            text="❌ Cancelar",
            command=dialog.destroy,
            bg="#FF5252",
            fg="white",
            font=("Segoe UI", 10),
            relief="flat",
            padx=15,
            pady=5,
            cursor="hand2"
        ).pack(side="left", padx=5)
    
    def _conectar(self):
        """Conecta a la base de datos MySQL"""
        with self.lock:
            try:
                if self.cursor:
                    try:
                        self.cursor.close()
                    except:
                        pass
                if self.connection:
                    try:
                        self.connection.close()
                    except:
                        pass
                
                self.connection = mysql.connector.connect(
                    host=self.host_var.get(),
                    port=int(self.port_var.get()),
                    user=self.user_var.get(),
                    password=self.password_var.get(),
                    database=self.database_var.get(),
                    connection_timeout=30,
                    autocommit=True,
                    use_pure=True,
                    consume_results=True
                )
                
                self.cursor = self.connection.cursor(dictionary=True, buffered=True)
                
                self.cursor.execute("SELECT 1")
                self.cursor.fetchall()
                
                self._cargar_colores_tipos()
                self._cargar_listas_completas()
                
                self.connected = True
                self.root.after(0, lambda: self.status_indicator.config(fg="#4CAF50"))
                self.root.after(0, lambda: self.status_label.config(text="Conectado", fg="#4CAF50"))
                logger.info("Conectado a MySQL")
                return True
                
            except Exception as e:
                self.connected = False
                self.connection = None
                self.cursor = None
                self.root.after(0, lambda: self.status_indicator.config(fg="#FF5252"))
                self.root.after(0, lambda: self.status_label.config(text="Desconectado", fg="#FF5252"))
                logger.error(f"Error de conexión: {e}")
                return False
    
    def _cargar_colores_tipos(self):
        """Carga los colores personalizados de cada tipo de falla"""
        try:
            if not self.connection or not self.cursor:
                return
            
            self.cursor.execute("SELECT nombre, color FROM tipos_falla")
            tipos = self.cursor.fetchall()
            
            self.tipos_colores.clear()
            for tipo in tipos:
                self.tipos_colores[tipo["nombre"]] = tipo["color"]
            
            logger.info(f"Cargados {len(self.tipos_colores)} colores de tipos de falla")
            
        except Exception as e:
            logger.error(f"Error cargando colores de tipos: {e}")
    
    def _cargar_listas_completas(self):
        """Carga todas las máquinas disponibles (hasta 200) y todos los tipos de falla"""
        try:
            if not self.connection or not self.cursor:
                return
            
            # Cargar tipos de falla desde la BD
            self.cursor.execute("SELECT nombre FROM tipos_falla ORDER BY orden")
            tipos = self.cursor.fetchall()
            self.tipos_disponibles = ["TODOS"] + [t["nombre"] for t in tipos]
            
            # Cargar máquinas (hasta 200)
            # Intentar obtener de config_licencia el límite
            self.cursor.execute("SELECT max_maquinas FROM config_licencia WHERE id = 1")
            row = self.cursor.fetchone()
            max_maquinas = row["max_maquinas"] if row else 200
            
            # Generar lista de máquinas del 1 al límite
            self.maquinas_disponibles = ["TODAS"] + [str(i) for i in range(1, max_maquinas + 1)]
            
            # Actualizar combos en UI
            self.root.after(0, lambda: self.filtro_maquina_combo.configure(values=self.maquinas_disponibles))
            self.root.after(0, lambda: self.filtro_tipo_combo.configure(values=self.tipos_disponibles))
            
            logger.info(f"Cargadas {len(self.maquinas_disponibles)-1} máquinas y {len(self.tipos_disponibles)-1} tipos")
            
        except Exception as e:
            logger.error(f"Error cargando listas: {e}")
    
    def _actualizar_listas_completas(self):
        """Actualiza las listas de máquinas y tipos"""
        self._cargar_listas_completas()
    
    def _get_color_para_tipo(self, tipo: str) -> str:
        """Obtiene el color asociado a un tipo de falla"""
        if tipo in self.tipos_colores:
            return self.tipos_colores[tipo]
        
        colores_default = {
            "Mantenimiento": "#FF9A00",
            "Producción": "#FF5252",
            "Calidad": "#4CAF50",
            "Materiales": "#2196F3",
            "Ingeniería": "#9C27B0"
        }
        
        if tipo in colores_default:
            return colores_default[tipo]
        
        hash_obj = hashlib.md5(tipo.encode())
        hash_int = int(hash_obj.hexdigest(), 16)
        hue = (hash_int % 360) / 360.0
        r, g, b = hsv_to_rgb(hue, 0.7, 0.6)
        return f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'
    
    def _iniciar_actualizacion(self):
        """Inicia el ciclo de actualización de datos"""
        def actualizar():
            while self.running:
                if self.connected:
                    try:
                        self._cargar_fallas_activas()
                    except Exception as e:
                        logger.error(f"Error actualizando datos: {e}")
                        self._conectar()
                time.sleep(2)
        
        thread = threading.Thread(target=actualizar, daemon=True)
        thread.start()
    
    def _cargar_fallas_activas(self):
        """Carga las fallas activas desde la base de datos"""
        with self.lock:
            if not self.connection or not self.cursor or not self.connected:
                return
            
            try:
                self.cursor.execute("SELECT 1")
                self.cursor.fetchall()
                
                query = """
                    SELECT 
                        maquina,
                        tipo,
                        inicio,
                        proceso,
                        fin,
                        estado,
                        numero_falla,
                        nota_pendiente,
                        fecha_pendiente
                    FROM fallas_activas
                    ORDER BY inicio DESC
                """
                
                self.cursor.execute(query)
                nuevas_fallas = self.cursor.fetchall()
                
                # Detectar nuevas fallas para reproducir sonido
                if self.sonidos_habilitados.get():
                    tipos_anteriores = {f.get("numero_falla"): f.get("tipo") for f in self.fallas_previas}
                    tipos_nuevos = {f.get("numero_falla"): f.get("tipo") for f in nuevas_fallas}
                    
                    # Buscar fallas que están en nuevas pero no en anteriores (nuevas fallas)
                    for num_falla, tipo in tipos_nuevos.items():
                        if num_falla not in tipos_anteriores:
                            # Nueva falla detectada!
                            logger.info(f"Nueva falla #{num_falla} detectada: {tipo}")
                            self.root.after(0, lambda t=tipo: self._reproducir_sonido_para_tipo(t))
                
                self.fallas_previas = nuevas_fallas.copy()
                self.fallas_activas = nuevas_fallas
                
                self.root.after(0, self._aplicar_filtros)
                self.root.after(0, self._actualizar_contador)
                
            except mysql.connector.Error as e:
                logger.error(f"Error consultando fallas: {e}")
                self.connected = False
                self.root.after(0, lambda: self.status_indicator.config(fg="#FF5252"))
                self.root.after(0, lambda: self.status_label.config(text="Desconectado", fg="#FF5252"))
                try:
                    if self.cursor:
                        self.cursor.close()
                    if self.connection:
                        self.connection.close()
                except:
                    pass
                self.cursor = None
                self.connection = None
    
    def _aplicar_filtros(self):
        """Aplica los filtros de máquina y tipo de falla"""
        maquina_filtro = self.filtro_maquina_var.get()
        tipo_filtro = self.filtro_tipo_var.get()
        
        # Filtrar fallas
        fallas_filtradas = self.fallas_activas.copy()
        
        if maquina_filtro != "TODAS":
            fallas_filtradas = [f for f in fallas_filtradas if f.get("maquina") == maquina_filtro]
        
        if tipo_filtro != "TODOS":
            fallas_filtradas = [f for f in fallas_filtradas if f.get("tipo") == tipo_filtro]
        
        # Actualizar indicador de filtros
        filtros_activos = []
        if maquina_filtro != "TODAS":
            filtros_activos.append(f"Máquina: {maquina_filtro}")
        if tipo_filtro != "TODOS":
            filtros_activos.append(f"Tipo: {tipo_filtro}")
        
        if filtros_activos:
            self.filtro_label.config(text=f"Filtros activos: {' | '.join(filtros_activos)}")
        else:
            self.filtro_label.config(text="")
        
        # Actualizar tabla
        self._actualizar_tabla_con_filtro(fallas_filtradas)
        
        # Actualizar contador
        count = len(fallas_filtradas)
        if count == 0:
            self.counter_label.config(text="✅ Sin fallas con filtros activos", fg="#4CAF50")
        else:
            self.counter_label.config(text=f"⚠️ {count} falla{'s' if count != 1 else ''} activa{'s' if count != 1 else ''}", fg="#FF5252")
    
    def _actualizar_tabla_con_filtro(self, fallas_filtradas):
        """Actualiza la tabla con las fallas filtradas"""
        if not hasattr(self, 'tree') or not self.tree.winfo_exists():
            return
        
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if not fallas_filtradas:
            self.tree.insert("", "end", values=("", "✅", "Sin fallas con los filtros actuales", "", "", "", ""), tags=("activa",))
            return
        
        # Configurar tags para cada tipo de falla
        current_font_size = self.font_size.get()
        for falla in fallas_filtradas:
            tipo = falla.get("tipo", "Desconocido")
            color = self._get_color_para_tipo(tipo)
            text_color = "#000000" if is_light_color(color) else "#FFFFFF"
            
            tag_name = f"tipo_{tipo.replace(' ', '_')}"
            if tag_name not in self.configured_tags:
                self.tree.tag_configure(tag_name, background=color, foreground=text_color, font=("Segoe UI", current_font_size, "bold"))
                self.configured_tags.add(tag_name)
        
        # Configurar tag para pendientes
        if "pendiente" not in self.configured_tags:
            self.tree.tag_configure("pendiente", background="#FFA500", foreground="white", font=("Segoe UI", current_font_size, "bold"))
            self.configured_tags.add("pendiente")
        
        # Insertar datos
        for falla in fallas_filtradas:
            tipo = falla.get("tipo", "Desconocido")
            tag_name = f"tipo_{tipo.replace(' ', '_')}"
            
            estado = falla.get("estado", "activa")
            if estado == "pendiente":
                estado_text = "🟠 Pendiente"
                tags = (tag_name, "pendiente")
            elif estado == "en_proceso":
                estado_text = "🟡 En Proceso"
                tags = (tag_name,)
            else:
                estado_text = "🔴 Activa"
                tags = (tag_name,)
            
            valores = (
                f"#{falla.get('numero_falla', '?')}",
                falla.get("maquina", "?"),
                tipo,
                solo_hora(falla.get("inicio", "")),
                solo_hora(falla.get("proceso", "")),
                solo_hora(falla.get("fin", "")),
                estado_text
            )
            
            item = self.tree.insert("", "end", values=valores, tags=tags)
            
            if falla.get("nota_pendiente"):
                self.tree.set(item, "Estado", f"{estado_text} 📝")
    
    def _actualizar_contador(self):
        """Actualiza el contador total de fallas (sin filtros)"""
        if self.counter_label and self.counter_label.winfo_exists():
            count = len(self.fallas_activas)
            if count == 0:
                self.counter_label.config(text="✅ Sin fallas activas", fg="#4CAF50")
            else:
                self.counter_label.config(text=f"⚠️ {count} falla{'s' if count != 1 else ''} activa{'s' if count != 1 else ''}", fg="#FF5252")
    
    def _toggle_fullscreen(self):
        """Alterna modo pantalla completa"""
        self.root.attributes('-fullscreen', not self.root.attributes('-fullscreen'))
        if self.root.attributes('-fullscreen'):
            self._ajustar_para_pantalla_completa(True)
        else:
            self._ajustar_para_pantalla_completa(False)
    
    def _salir_fullscreen(self):
        """Sale del modo pantalla completa"""
        if self.root.attributes('-fullscreen'):
            self.root.attributes('-fullscreen', False)
            self._ajustar_para_pantalla_completa(False)
    
    def _ajustar_para_pantalla_completa(self, fullscreen: bool):
        """Ajusta el tamaño de fuente para pantalla completa"""
        style = ttk.Style()
        current_size = self.font_size.get()
        
        if fullscreen:
            # En pantalla completa, aumentar temporalmente el tamaño visual
            display_size = int(current_size * 1.5)
            style.configure("Monitor.Treeview", font=("Segoe UI", display_size), rowheight=display_size + 50)
            style.configure("Monitor.Treeview.Heading", font=("Segoe UI", display_size + 2, "bold"))
            self.counter_label.config(font=("Segoe UI", int(display_size * 1.5), "bold"))
            self.clock_label.config(font=("Segoe UI", int(display_size * 1.5), "bold"))
            self.date_label.config(font=("Segoe UI", int(display_size * 1.5)))
            
            for col, ancho in zip(("Máquina", "Tipo", "Inicio", "Proceso", "Fin", "Estado"), [150, 280, 180, 180, 180, 180]):
                self.tree.column(col, width=ancho)
        else:
            # Restaurar tamaño normal
            style.configure("Monitor.Treeview", font=("Segoe UI", current_size), rowheight=current_size + 33)
            style.configure("Monitor.Treeview.Heading", font=("Segoe UI", current_size + 1, "bold"))
            self.counter_label.config(font=("Segoe UI", int(current_size * 1.5), "bold"))
            self.clock_label.config(font=("Segoe UI", int(current_size * 1.5), "bold"))
            self.date_label.config(font=("Segoe UI", int(current_size * 1.5)))
            
            base_widths = [80, 100, 200, 120, 120, 120, 120]
            factor = max(0.8, min(1.5, current_size / 12))
            anchos = [int(w * factor) for w in base_widths]
            for col, ancho in zip(("#", "Máquina", "Tipo", "Inicio", "Proceso", "Fin", "Estado"), anchos):
                self.tree.column(col, width=ancho)


def main():
    """Punto de entrada principal"""
    try:
        import socket
        import sys
        
        lock_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            lock_socket.bind(('127.0.0.1', 54323))
        except socket.error:
            print("⚠️ Ya hay una instancia del monitor ejecutándose")
            sys.exit(0)
        
        app = MonitorRemoto()
        
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        import traceback
        traceback.print_exc()
        input("Presiona Enter para salir...")


if __name__ == "__main__":
    main()