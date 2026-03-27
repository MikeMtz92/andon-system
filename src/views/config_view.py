# src/views/config_view.py

import tkinter as tk
from tkinter import ttk, messagebox, colorchooser, filedialog
import threading
import os
import logging

from src.utils.widgets import ModernButton, ModernEntry, ModernCombobox
from src.utils.helpers import is_light_color, lighten_color
from src.utils.constants import TEMAS_PREDEFINIDOS, DB_CONFIG_DEFAULT

logger = logging.getLogger(__name__)

class ConfigView:
    """Ventana de configuración del sistema"""
    
    def __init__(self, parent, controller, theme_service, falla_controller):
        self.parent = parent
        self.controller = controller
        self.theme = theme_service
        self.falla_controller = falla_controller
        
        self.ventana = tk.Toplevel(parent)
        self.ventana.title("Configuración del Sistema")
        self.ventana.geometry("800x900")
        self.ventana.configure(bg=self.theme.colores["fondo"])
        self.ventana.resizable(True, True)
        self.ventana.minsize(700, 700)
        self.ventana.transient(parent)
        self.ventana.grab_set()
        
        # Centrar ventana
        self.ventana.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (800 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (900 // 2)
        self.ventana.geometry(f"+{x}+{y}")
        
        # Variables para configuración
        self._inicializar_variables()
        self._setup_ui()
    
        # Forzar actualización de la ventana
        self.ventana.update_idletasks()
        self.ventana.update()
        
        print("DEBUG: ConfigView completamente inicializada")

        
    def _inicializar_variables(self):
        """Inicializa las variables de la UI"""
        # Base de datos
        self.db_tipo_var = tk.StringVar(value="mysql")
        self.db_host_var = tk.StringVar(value=self.controller.db_config["host"])
        self.db_port_var = tk.StringVar(value=str(self.controller.db_config["port"]))
        self.db_user_var = tk.StringVar(value=self.controller.db_config["usuario"])
        self.db_pass_var = tk.StringVar(value=self.controller.db_config["password"])
        self.db_name_var = tk.StringVar(value=self.controller.db_config["base_datos"])
        self.db_timeout_var = tk.StringVar(value=str(self.controller.db_config.get("timeout", 30)))
        self.db_ssl_var = tk.BooleanVar(value=self.controller.db_config.get("usar_ssl", False))
        
        # Temas
        self.tema_selector_var = tk.StringVar(value=self.theme.tema_actual)
        
        # Mapeo de botones
        self.mapeo_vars = {}
        
        # Colores personalizados (para la UI)
        self.color_entries = {}
        
    def _setup_ui(self):
        """Configura la interfaz de usuario"""
        print("DEBUG: _setup_ui INICIADO")
        
        # Contenedor principal con scroll
        main_container = tk.Frame(self.ventana, bg=self.theme.colores["fondo"])
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(main_container,
                text="⚙️ Configuración del Sistema",
                bg=self.theme.colores["fondo"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 18, "bold")).pack(pady=(0, 20))
        
        # Frame para canvas y scrollbar
        canvas_frame = tk.Frame(main_container, bg=self.theme.colores["fondo"])
        canvas_frame.pack(fill="both", expand=True)
        
        # Canvas y scrollbar
        canvas = tk.Canvas(canvas_frame, bg=self.theme.colores["fondo"], highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.theme.colores["fondo"])
        
        # Configurar scrollable frame
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        # Crear ventana en el canvas - IMPORTANTE: darle un tamaño inicial
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # Configurar canvas para que se expanda
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # ===== SONIDOS (PRO) =====
        self._crear_seccion_sonidos(scrollable_frame)
        
        def configure_canvas(event):
            # Actualizar el ancho del canvas
            canvas.itemconfig(canvas_window, width=event.width)
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        canvas.bind('<Configure>', configure_canvas)
        
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind("<MouseWheel>", _on_mousewheel)
        
        print("DEBUG: Canvas configurado")
        
        # ===== SECCIONES =====
        print("DEBUG: Creando sección BD")
        self._crear_seccion_bd(scrollable_frame)
        
        print("DEBUG: Creando sección nombre")
        self._crear_seccion_nombre(scrollable_frame)
        
        print("DEBUG: Creando sección tipos falla")
        self._crear_seccion_tipos_falla(scrollable_frame)
        
        print("DEBUG: Creando sección mapeo")
        self._crear_seccion_mapeo(scrollable_frame)
        
        print("DEBUG: Creando sección temas")
        self._crear_seccion_temas(scrollable_frame)
        
        print("DEBUG: Creando botones acción")
        self._crear_botones_accion(scrollable_frame)
        
        # Empaquetar canvas y scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        print("DEBUG: _setup_ui FINALIZADO")
     
    def _crear_seccion_bd(self, parent):
        """Crea la sección de configuración de base de datos"""
        print("DEBUG: _crear_seccion_bd - Creando tarjeta")
        
        card = tk.Frame(parent, bg=self.theme.colores["card"], relief="flat", bd=1,
                       highlightbackground=self.theme.colores["texto_secundario"])
        card.pack(fill="x", padx=10, pady=(0, 15))
        
        tk.Label(card,
                text="💾 Configuración de Base de Datos",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=15, pady=(15, 10))
        
        # Tipo de BD (fijo MySQL)
        tipo_frame = tk.Frame(card, bg=self.theme.colores["card"])
        tipo_frame.pack(fill="x", padx=15, pady=5)
        
        tk.Label(tipo_frame,
                text="Tipo de BD:",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto_secundario"],
                font=("Segoe UI", 10),
                width=15,
                anchor="w").pack(side="left")
        
        tk.Label(tipo_frame,
                text="MySQL (obligatorio)",
                bg=self.theme.colores["success"],
                fg="white",
                font=("Segoe UI", 10, "bold"),
                padx=10,
                pady=2).pack(side="left", padx=5)
        
        # Campos MySQL
        mysql_frame = tk.Frame(card, bg=self.theme.colores["card"])
        mysql_frame.pack(fill="x", padx=15, pady=10)
        
        campos = [
            ("Host:", self.db_host_var, 25),
            ("Puerto:", self.db_port_var, 10),
            ("Usuario:", self.db_user_var, 25),
            ("Contraseña:", self.db_pass_var, 25, True),
            ("Base de Datos:", self.db_name_var, 25),
            ("Timeout (seg):", self.db_timeout_var, 10)
        ]
        
        for campo in campos:
            frame = tk.Frame(mysql_frame, bg=self.theme.colores["card"])
            frame.pack(fill="x", pady=3)
            
            tk.Label(frame,
                    text=campo[0],
                    bg=self.theme.colores["card"],
                    fg=self.theme.colores["texto_secundario"],
                    font=("Segoe UI", 10),
                    width=15,
                    anchor="w").pack(side="left")
            
            entry = tk.Entry(frame,
                           textvariable=campo[1],
                           width=campo[2],
                           bg=self.theme.colores.get("superficie3", "#2d3047"),
                           fg=self.theme.colores["texto"],
                           relief="flat",
                           font=("Segoe UI", 10))
            if len(campo) > 3 and campo[3]:
                entry.config(show="•")
            entry.pack(side="left", padx=5)
        
        # SSL
        ssl_frame = tk.Frame(mysql_frame, bg=self.theme.colores["card"])
        ssl_frame.pack(fill="x", pady=5)
        
        tk.Checkbutton(ssl_frame,
                      text="Usar SSL",
                      variable=self.db_ssl_var,
                      bg=self.theme.colores["card"],
                      fg=self.theme.colores["texto"],
                      selectcolor=self.theme.colores["accento"],
                      font=("Segoe UI", 10)).pack(anchor="w", padx=20)
        
        # Botones de acción BD
        btn_frame = tk.Frame(mysql_frame, bg=self.theme.colores["card"])
        btn_frame.pack(fill="x", pady=10)
        
        tk.Button(btn_frame,
                 text="🔌 Probar Conexión",
                 bg=self.theme.colores["success"],
                 fg=self.theme.colores["texto"],
                 font=("Segoe UI", 10),
                 relief="flat",
                 padx=15,
                 pady=5,
                 cursor="hand2",
                 command=self._probar_conexion).pack(side="left", padx=5)
        
        # Etiqueta de estado
        self.db_estado_label = tk.Label(mysql_frame,
                                       text="",
                                       bg=self.theme.colores["card"],
                                       fg=self.theme.colores["texto"],
                                       font=("Segoe UI", 9))
        self.db_estado_label.pack(anchor="w", padx=15, pady=5)
        
    def _crear_seccion_nombre(self, parent):
        """Crea la sección de nombre del sistema"""
        card = tk.Frame(parent, bg=self.theme.colores["card"], relief="flat", bd=1,
                       highlightbackground=self.theme.colores["texto_secundario"])
        card.pack(fill="x", padx=10, pady=(0, 15))
        
        tk.Label(card,
                text="📛 Nombre del Sistema",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15, pady=(15, 5))
        
        frame = tk.Frame(card, bg=self.theme.colores["card"])
        frame.pack(fill="x", padx=15, pady=(0, 15))
        
        self.entry_nombre = tk.Entry(frame,
                                    width=30,
                                    bg=self.theme.colores.get("superficie3", "#2d3047"),
                                    fg=self.theme.colores["texto"],
                                    relief="flat",
                                    font=("Segoe UI", 10))
        self.entry_nombre.insert(0, self.theme.colores.get("nombre_sistema", "ANDON SYSTEM"))
        self.entry_nombre.pack(side="left", padx=(0, 10))
        
        tk.Button(frame,
                 text="Cambiar",
                 bg=self.theme.colores["accento"],
                 fg=self.theme.colores["texto"],
                 font=("Segoe UI", 10),
                 relief="flat",
                 padx=15,
                 pady=5,
                 cursor="hand2",
                 command=self._cambiar_nombre).pack(side="left")
    def _crear_seccion_tipos_falla(self, parent):
        """Crea la sección de tipos de falla"""
        print("DEBUG: _crear_seccion_tipos_falla INICIADO")
        
        card = tk.Frame(parent, bg=self.theme.colores["card"], relief="flat", bd=1,
                    highlightbackground=self.theme.colores["texto_secundario"])
        card.pack(fill="x", padx=10, pady=(0, 15))
        
        # Límite de licencia
        limite_frame = tk.Frame(card, bg=self.theme.colores["card"])
        limite_frame.pack(fill="x", padx=15, pady=(10, 0))
        
        try:
            tipos_data = self.falla_controller.falla_model.cargar_tipos_falla()
            print(f"DEBUG: tipos_data obtenido: {tipos_data}")
            tipos_actuales = len(tipos_data)
        except Exception as e:
            print(f"ERROR obteniendo tipos: {e}")
            tipos_actuales = 0
        
        max_tipos = self.controller.licencia_controller.max_tipos_falla
        print(f"DEBUG: tipos_actuales={tipos_actuales}, max_tipos={max_tipos}")
        
        color_limite = self.theme.colores["success"] if tipos_actuales < max_tipos else self.theme.colores["danger"]
        
        tk.Label(limite_frame,
                text=f"📊 Tipos de falla permitidos: {tipos_actuales}/{max_tipos}",
                bg=self.theme.colores["card"],
                fg=color_limite,
                font=("Segoe UI", 11, "bold")).pack(anchor="w")
        
        if tipos_actuales >= max_tipos:
            tk.Label(limite_frame,
                    text="⚠️ Límite alcanzado. Elimina algún tipo para agregar más.",
                    bg=self.theme.colores["card"],
                    fg=self.theme.colores["warning"],
                    font=("Segoe UI", 9, "italic")).pack(anchor="w", pady=(2, 5))
        
        tk.Label(card,
                text="Tipos de Falla y sus Colores:",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15, pady=(5, 10))
        
        # Lista de tipos
        self.tipos_list_frame = tk.Frame(card, bg=self.theme.colores["card"])
        self.tipos_list_frame.pack(fill="x", padx=15, pady=5)
        
        print("DEBUG: Llamando a _cargar_lista_tipos")
        self._cargar_lista_tipos()
        
        # Botón agregar tipo
        btn_frame = tk.Frame(card, bg=self.theme.colores["card"])
        btn_frame.pack(fill="x", padx=15, pady=(10, 15))
        
        tk.Button(btn_frame,
                text="➕ Agregar Tipo",
                bg=self.theme.colores["success"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 9),
                relief="flat",
                padx=10,
                pady=5,
                cursor="hand2",
                command=self._agregar_tipo).pack(side="left", padx=5)
        
        print("DEBUG: _crear_seccion_tipos_falla FINALIZADO")
    
    def _cargar_lista_tipos(self):
        """Carga la lista de tipos de falla con sus colores"""
        for widget in self.tipos_list_frame.winfo_children():
            widget.destroy()
        
        tipos_data = self.falla_controller.falla_model.cargar_tipos_falla()
        
        for i, tipo in enumerate(tipos_data):
            frame = tk.Frame(self.tipos_list_frame, bg=self.theme.colores["card"])
            frame.pack(fill="x", pady=2)
            
            tk.Label(frame,
                    text=f"{i+1}. ",
                    bg=self.theme.colores["card"],
                    fg=self.theme.colores["texto_secundario"],
                    font=("Segoe UI", 9)).pack(side="left", padx=(5, 0))
            
            entry_var = tk.StringVar(value=tipo["nombre"])
            entry = tk.Entry(frame,
                           textvariable=entry_var,
                           bg=self.theme.colores.get("superficie3", "#2d3047"),
                           fg=self.theme.colores["texto"],
                           relief="flat",
                           font=("Segoe UI", 9),
                           width=15)
            entry.pack(side="left", padx=(0, 5))
            entry.var = entry_var
            entry.index = i
            entry.original_nombre = tipo["nombre"]
            
            # Previsualización de color
            color_frame = tk.Frame(frame, bg=tipo["color"], width=50, height=20)
            color_frame.pack(side="left", padx=(5, 5))
            color_frame.pack_propagate(False)
            
            color_label = tk.Label(color_frame,
                                 text="Color",
                                 bg=tipo["color"],
                                 fg="#000000" if is_light_color(tipo["color"]) else "#FFFFFF",
                                 font=("Segoe UI", 8))
            color_label.pack(expand=True, fill="both")
            
            # Botón cambiar color
            tk.Button(frame,
                    text="🎨",
                    bg=self.theme.colores["card"],
                    fg=self.theme.colores["texto"],
                    font=("Segoe UI", 8),
                    relief="flat",
                    width=2,
                    cursor="hand2",
                    command=lambda t=tipo["nombre"], l=color_label, idx=i: 
                           self._cambiar_color_tipo(t, l, idx)).pack(side="left", padx=(0, 5))
            
            # Botón eliminar
            tk.Button(frame,
                    text="✕",
                    bg=self.theme.colores["danger"],
                    fg=self.theme.colores["texto"],
                    font=("Segoe UI", 8),
                    relief="flat",
                    width=2,
                    cursor="hand2",
                    command=lambda idx=i, nombre=tipo["nombre"]: 
                           self._eliminar_tipo(idx, nombre)).pack(side="left", padx=(0, 5))
            
            entry.color_label = color_label
            entry.color = tipo["color"]
            
    def _crear_seccion_mapeo(self, parent):
        """Crea la sección de mapeo de botones"""
        card = tk.Frame(parent, bg=self.theme.colores["card"], relief="flat", bd=1,
                       highlightbackground=self.theme.colores["texto_secundario"])
        card.pack(fill="x", padx=10, pady=(0, 15))
        
        tk.Label(card,
                text="🔌 Configuración de Botones Físicos",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=15, pady=(15, 10))
        
        tk.Label(card,
                text="Asigna cada botón físico a un tipo de falla:",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto_secundario"],
                font=("Segoe UI", 10)).pack(anchor="w", padx=15, pady=(0, 10))
        
        mapeo_frame = tk.Frame(card, bg=self.theme.colores["card"])
        mapeo_frame.pack(fill="x", padx=15, pady=5)
        
        tipos_data = self.falla_controller.falla_model.cargar_tipos_falla()
        tipos_nombres = [t["nombre"] for t in tipos_data]
        
        for i in range(1, 6):
            row = tk.Frame(mapeo_frame, bg=self.theme.colores["card"])
            row.pack(fill="x", pady=3)
            
            tk.Label(row,
                    text=f"Botón {i}:",
                    bg=self.theme.colores["card"],
                    fg=self.theme.colores["texto"],
                    font=("Segoe UI", 10, "bold"),
                    width=10,
                    anchor="w").pack(side="left", padx=(0, 10))
            
            var = tk.StringVar()
            mapeo_actual = self.falla_controller.mapeo_botones.get(i, "")
            if mapeo_actual:
                var.set(mapeo_actual)
            
            combo = ttk.Combobox(row,
                                textvariable=var,
                                values=tipos_nombres,
                                width=25,
                                state="readonly")
            combo.pack(side="left", padx=5)
            
            self.mapeo_vars[i] = var
        
        info_label = tk.Label(card,
                             text="Nota: El mapeo se guardará al presionar 'Guardar Configuración'",
                             bg=self.theme.colores["card"],
                             fg=self.theme.colores["warning"],
                             font=("Segoe UI", 9, "italic"))
        info_label.pack(anchor="w", padx=15, pady=(10, 15))
        
    def _crear_seccion_temas(self, parent):
        """Crea la sección de temas y colores"""
        card = tk.Frame(parent, bg=self.theme.colores["card"], relief="flat", bd=1,
                       highlightbackground=self.theme.colores["texto_secundario"])
        card.pack(fill="x", padx=10, pady=(0, 15))
        
        tk.Label(card,
                text="🎨 Temas y Colores",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=15, pady=(15, 10))
        
        # Selector de tema
        tema_frame = tk.Frame(card, bg=self.theme.colores["card"])
        tema_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        tk.Label(tema_frame,
                text="Tema Predefinido:",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 10),
                width=20,
                anchor="w").pack(side="left")
        
        opciones_temas = list(TEMAS_PREDEFINIDOS.keys()) + ["personalizado"]
        tema_combo = ttk.Combobox(tema_frame,
                                 textvariable=self.tema_selector_var,
                                 values=opciones_temas,
                                 state="readonly",
                                 width=15)
        tema_combo.pack(side="left", padx=5)
        
        tk.Button(tema_frame,
                 text="Aplicar Tema",
                 bg=self.theme.colores["accento"],
                 fg=self.theme.colores["texto"],
                 font=("Segoe UI", 9),
                 relief="flat",
                 padx=10,
                 pady=2,
                 cursor="hand2",
                 command=self._aplicar_tema).pack(side="left", padx=5)
        
        tk.Label(card,
                text="Personalización Avanzada:",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        # Colores personalizables
        colores_config = [
            ("Fondo Principal", "fondo"),
            ("Superficie 1 (Sidebar)", "superficie1"),
            ("Superficie 2 (Tarjetas)", "superficie2"),
            ("Superficie 3 (Inputs)", "superficie3"),
            ("Texto Principal", "texto_principal"),
            ("Texto Secundario", "texto_secundario"),
            ("Acento Principal", "acento_principal"),
            ("Éxito", "exito"),
            ("Advertencia", "advertencia"),
            ("Peligro", "peligro"),
            ("Pendiente", "pendiente"),
        ]
        
        colores_container = tk.Frame(card, bg=self.theme.colores["card"])
        colores_container.pack(fill="x", padx=15, pady=(0, 15))
        
        for nombre_mostrar, clave_paleta in colores_config:
            color_actual = self.theme.paleta_actual.get(clave_paleta, "#000000")
            
            frame = tk.Frame(colores_container, bg=self.theme.colores["card"])
            frame.pack(fill="x", pady=2)
            
            tk.Label(frame,
                    text=nombre_mostrar + ":",
                    bg=self.theme.colores["card"],
                    fg=self.theme.colores["texto"],
                    font=("Segoe UI", 9),
                    width=22,
                    anchor="w").pack(side="left")
            
            preview = tk.Frame(frame, bg=color_actual, width=40, height=20)
            preview.pack(side="left", padx=(5, 5))
            preview.pack_propagate(False)
            
            preview_label = tk.Label(preview,
                                    text=" ",
                                    bg=color_actual)
            preview_label.pack(expand=True, fill="both")
            
            tk.Button(frame,
                     text="Cambiar",
                     bg=self.theme.colores["card"],
                     fg=self.theme.colores["texto"],
                     font=("Segoe UI", 8),
                     relief="flat",
                     padx=8,
                     pady=1,
                     cursor="hand2",
                     command=lambda k=clave_paleta, p=preview: 
                            self._cambiar_color_personalizado(k, p)).pack(side="left", padx=(2, 0))
            
            self.color_entries[clave_paleta] = preview
            
    def _crear_botones_accion(self, parent):
        """Crea los botones de acción al final"""
        card = tk.Frame(parent, bg=self.theme.colores["card"], relief="flat", bd=1,
                       highlightbackground=self.theme.colores["texto_secundario"])
        card.pack(fill="x", padx=10, pady=(0, 20))
        
        btn_frame = tk.Frame(card, bg=self.theme.colores["card"])
        btn_frame.pack(fill="x", padx=15, pady=15)
        
        tk.Button(btn_frame,
                 text="💾 Guardar Configuración",
                 bg=self.theme.colores["success"],
                 fg=self.theme.colores["texto"],
                 font=("Segoe UI", 11, "bold"),
                 relief="flat",
                 padx=20,
                 pady=10,
                 cursor="hand2",
                 command=self._guardar).pack(side="left", padx=5)
        
        tk.Button(btn_frame,
                 text="↻ Restaurar Valores por Defecto",
                 bg=self.theme.colores["warning"],
                 fg=self.theme.colores["negro"],
                 font=("Segoe UI", 11),
                 relief="flat",
                 padx=20,
                 pady=10,
                 cursor="hand2",
                 command=self._restaurar_default).pack(side="left", padx=5)
        
        tk.Button(btn_frame,
                 text="❌ Cancelar",
                 bg=self.theme.colores["danger"],
                 fg=self.theme.colores["texto"],
                 font=("Segoe UI", 11),
                 relief="flat",
                 padx=20,
                 pady=10,
                 cursor="hand2",
                 command=self._cerrar).pack(side="right", padx=5)
        
    def _probar_conexion(self):
        """Prueba la conexión a MySQL"""
        config = {
            "host": self.db_host_var.get(),
            "port": int(self.db_port_var.get()),
            "usuario": self.db_user_var.get(),
            "password": self.db_pass_var.get(),
            "base_datos": self.db_name_var.get(),
            "timeout": int(self.db_timeout_var.get()),
            "usar_ssl": self.db_ssl_var.get()
        }
        
        def test():
            try:
                import mysql.connector
                conn = mysql.connector.connect(
                    host=config["host"],
                    port=config["port"],
                    user=config["usuario"],
                    password=config["password"],
                    database=config["base_datos"],
                    connection_timeout=config["timeout"],
                    ssl_disabled=not config["usar_ssl"]
                )
                conn.close()
                self.ventana.after(0, lambda: self.db_estado_label.config(
                    text="✅ Conexión exitosa", fg=self.theme.colores["success"]))
                self.ventana.after(0, lambda: messagebox.showinfo("Éxito", "Conexión exitosa"))
            except Exception as e:
                self.ventana.after(0, lambda: self.db_estado_label.config(
                    text=f"❌ Error: {str(e)[:50]}", fg=self.theme.colores["danger"]))
                self.ventana.after(0, lambda: messagebox.showerror("Error", f"No se pudo conectar:\n{str(e)}"))
        
        threading.Thread(target=test, daemon=True).start()
        
    def _cambiar_nombre(self):
        """Cambia el nombre del sistema"""
        nuevo = self.entry_nombre.get().strip()
        if nuevo:
            self.theme.colores["nombre_sistema"] = nuevo
            self.theme.paleta_actual["nombre_sistema"] = nuevo
            messagebox.showinfo("Éxito", f"Nombre cambiado a: {nuevo}")
            
    def _cambiar_color_tipo(self, tipo, label, index):
        """Cambia el color de un tipo de falla"""
        from src.utils.constants import COLORES_DEFAULT
        color_key = f"{tipo.lower().replace(' ', '_')}_color"
        color_actual = self.theme.colores.get(color_key, COLORES_DEFAULT.get("accento", "#e94560"))
        
        color = colorchooser.askcolor(title=f"Color para {tipo}", initialcolor=color_actual)
        if color and color[1]:
            self.theme.colores[color_key] = color[1]
            label.config(bg=color[1], 
                        fg="#000000" if is_light_color(color[1]) else "#FFFFFF")
            
    def _eliminar_tipo(self, index, nombre):
        """Elimina un tipo de falla"""
        if not messagebox.askyesno("Confirmar", 
                                   f"¿Eliminar el tipo '{nombre}'?\n\n"
                                   "Se eliminarán todos los registros asociados."):
            return
        
        # Eliminar de la base de datos
        conn = self.controller.db.get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM fallas WHERE tipo = %s", (nombre,))
                cursor.execute("DELETE FROM tipos_falla WHERE nombre = %s", (nombre,))
                conn.commit()
                conn.close()
            except Exception as e:
                logger.error(f"Error eliminando tipo: {e}")
                if conn:
                    conn.close()
        
        # Recargar lista
        self._cargar_lista_tipos()
        
    def _agregar_tipo(self):
        """Agrega un nuevo tipo de falla"""
        from src.utils.constants import FALLAS_DEFAULT, COLORES_DEFAULT
        
        max_tipos = self.controller.licencia_controller.max_tipos_falla
        tipos_actuales = len(self.falla_controller.falla_model.cargar_tipos_falla())
        
        if tipos_actuales >= max_tipos:
            messagebox.showwarning("Límite Alcanzado",
                                  f"Has alcanzado el límite de {max_tipos} tipos de falla")
            return
        
        # Diálogo para nuevo tipo
        dialog = tk.Toplevel(self.ventana)
        dialog.title("Nuevo Tipo de Falla")
        dialog.geometry("400x200")
        dialog.configure(bg=self.theme.colores["fondo"])
        dialog.transient(self.ventana)
        dialog.grab_set()
        
        tk.Label(dialog,
                text="➕ Agregar Nuevo Tipo de Falla",
                bg=self.theme.colores["fondo"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 14, "bold")).pack(pady=20)
        
        tk.Label(dialog,
                text="Nombre del nuevo tipo:",
                bg=self.theme.colores["fondo"],
                fg=self.theme.colores["texto_secundario"],
                font=("Segoe UI", 10)).pack()
        
        entry = tk.Entry(dialog,
                        width=30,
                        bg=self.theme.colores.get("superficie3", "#2d3047"),
                        fg=self.theme.colores["texto"],
                        relief="flat",
                        font=("Segoe UI", 10))
        entry.pack(pady=10)
        entry.focus()
        
        def confirmar():
            nuevo = entry.get().strip()
            if not nuevo:
                messagebox.showwarning("Aviso", "Ingresa un nombre", parent=dialog)
                return
            
            # Guardar en BD
            import random
            color = f"#{random.randint(0, 255):02x}{random.randint(0, 255):02x}{random.randint(0, 255):02x}"
            
            conn = self.controller.db.get_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO tipos_falla (nombre, color, orden) VALUES (%s, %s, %s)",
                                 (nuevo, color, tipos_actuales))
                    conn.commit()
                    conn.close()
                except Exception as e:
                    logger.error(f"Error agregando tipo: {e}")
                    if conn:
                        conn.close()
            
            dialog.destroy()
            self._cargar_lista_tipos()
            messagebox.showinfo("✅ Éxito", f"Tipo '{nuevo}' agregado")
        
        tk.Button(dialog,
                 text="✅ Agregar",
                 bg=self.theme.colores["success"],
                 fg=self.theme.colores["texto"],
                 font=("Segoe UI", 11, "bold"),
                 relief="flat",
                 padx=20,
                 pady=8,
                 cursor="hand2",
                 command=confirmar).pack(pady=20)
        
        dialog.bind('<Return>', lambda e: confirmar())
        
    def _aplicar_tema(self):
        """Aplica un tema predefinido"""
        tema = self.tema_selector_var.get()
        if tema in TEMAS_PREDEFINIDOS:
            self.theme.aplicar_tema(tema)
            
            # Actualizar previsualizaciones
            for clave, preview in self.color_entries.items():
                color = self.theme.paleta_actual.get(clave, "#000000")
                preview.config(bg=color)
                for child in preview.winfo_children():
                    if isinstance(child, tk.Label):
                        child.config(bg=color)
            
            messagebox.showinfo("Tema Aplicado", 
                              f"Tema '{TEMAS_PREDEFINIDOS[tema]['nombre']}' aplicado")
            
    def _cambiar_color_personalizado(self, clave, preview):
        """Cambia un color personalizado"""
        color_actual = preview.cget('bg')
        color = colorchooser.askcolor(title="Seleccionar color", initialcolor=color_actual)
        if color and color[1]:
            self.theme.actualizar_color(clave, color[1])
            preview.config(bg=color[1])
            for child in preview.winfo_children():
                if isinstance(child, tk.Label):
                    child.config(bg=color[1])
            self.tema_selector_var.set("personalizado")
            
    def _guardar(self):
        """Guarda toda la configuración"""
        try:
            # 1. Guardar configuración de BD
            self.controller.db_config.update({
                "host": self.db_host_var.get(),
                "port": int(self.db_port_var.get()),
                "usuario": self.db_user_var.get(),
                "password": self.db_pass_var.get(),
                "base_datos": self.db_name_var.get(),
                "timeout": int(self.db_timeout_var.get()),
                "usar_ssl": self.db_ssl_var.get()
            })
            
            from src.models.config_model import ConfigModel
            ConfigModel.guardar_config_db(self.controller.db_config)
            
            # 2. Guardar tipos de falla
            tipos_nuevos = []
            for widget in self.tipos_list_frame.winfo_children():
                if isinstance(widget, tk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Entry) and hasattr(child, 'var'):
                            nombre = child.var.get().strip()
                            if nombre and hasattr(child, 'color'):
                                tipos_nuevos.append({"nombre": nombre, "color": child.color})
            
            if tipos_nuevos:
                self.falla_controller.falla_model.guardar_tipos_falla(tipos_nuevos)
            
            # 3. Guardar mapeo de botones
            nuevo_mapeo = {}
            for num, var in self.mapeo_vars.items():
                tipo = var.get().strip()
                if tipo:
                    nuevo_mapeo[num] = tipo
            
            self.falla_controller.falla_model.guardar_mapeo_botones(nuevo_mapeo)
            self.falla_controller.mapeo_botones = nuevo_mapeo
            
            # 4. Guardar nombre del sistema
            nombre = self.entry_nombre.get().strip()
            if nombre:
                self.theme.colores["nombre_sistema"] = nombre
            
            # 5. Guardar configuración del sistema
            config_sistema = self.theme.generar_config_sistema()
            self.controller.config_model.guardar_config_sistema(config_sistema)
            
            messagebox.showinfo("✅ Éxito", "Configuración guardada correctamente")
            self._cerrar()
            
        except Exception as e:
            logger.error(f"Error guardando configuración: {e}")
            messagebox.showerror("Error", f"No se pudo guardar: {str(e)}")
            
    def _restaurar_default(self):
        """Restaura valores por defecto"""
        if not messagebox.askyesno("Confirmar",
                                   "¿Restaurar valores por defecto?\n"
                                   "Se perderán todos los cambios personalizados."):
            return
        
        from src.utils.constants import DB_CONFIG_DEFAULT, FALLAS_DEFAULT, COLORES_DEFAULT
        
        # Restaurar valores en UI
        self.db_host_var.set(DB_CONFIG_DEFAULT["host"])
        self.db_port_var.set(str(DB_CONFIG_DEFAULT["port"]))
        self.db_user_var.set(DB_CONFIG_DEFAULT["usuario"])
        self.db_pass_var.set(DB_CONFIG_DEFAULT["password"])
        self.db_name_var.set(DB_CONFIG_DEFAULT["base_datos"])
        self.db_timeout_var.set(str(DB_CONFIG_DEFAULT["timeout"]))
        self.db_ssl_var.set(DB_CONFIG_DEFAULT["usar_ssl"])
        
        self.entry_nombre.delete(0, tk.END)
        self.entry_nombre.insert(0, "ANDON SYSTEM")
        
        # Restaurar tema
        self.theme.aplicar_tema("oscuro")
        self.tema_selector_var.set("oscuro")
        
        messagebox.showinfo("✅ Listo", "Valores restaurados. Guarda la configuración para aplicar.")
        
    def _cerrar(self):
        """Cierra la ventana de configuración"""
        try:
            self.ventana.destroy()
        except:
            pass
        
    def _crear_seccion_sonidos(self, parent):
        """Crea la sección para configurar sonidos por tipo de falla (solo PRO)"""
        if not self.controller.licencia_controller.puede_generar_esp32:  # Usamos 'puede_generar_esp32' como proxy de PRO
            return
        
        card = tk.Frame(parent, bg=self.theme.colores["card"], relief="flat", bd=1,
                       highlightbackground=self.theme.colores["texto_secundario"])
        card.pack(fill="x", padx=10, pady=(0, 15))
        
        tk.Label(card,
                text="🔊 Sonidos de Alarma por Tipo de Falla (PRO)",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=15, pady=(15, 10))
        
        tk.Label(card,
                text="Asigna un archivo de sonido (MP3 o WAV) a cada tipo de falla:",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto_secundario"],
                font=("Segoe UI", 10)).pack(anchor="w", padx=15, pady=(0, 10))
        
        # Frame para los selectores de sonido
        self.sonidos_frame = tk.Frame(card, bg=self.theme.colores["card"])
        self.sonidos_frame.pack(fill="x", padx=15, pady=5)
        
        # Cargar tipos de falla
        tipos_data = self.falla_controller.falla_model.cargar_tipos_falla()
        self.sonido_vars = {}
        
        # Cargar configuraciones existentes
        self.sonidos_configurados = self.falla_controller.sonidos_configurados
        
        for tipo in tipos_data:
            nombre = tipo["nombre"]
            frame = tk.Frame(self.sonidos_frame, bg=self.theme.colores["card"])
            frame.pack(fill="x", pady=5)
            
            # Indicador de color
            color = self.theme.get_color_para_tipo(nombre)
            tk.Label(frame,
                    text="●",
                    fg=color,
                    bg=self.theme.colores["card"],
                    font=("Segoe UI", 12, "bold")).pack(side="left", padx=(0, 10))
            
            # Etiqueta del tipo
            tk.Label(frame,
                    text=nombre + ":",
                    bg=self.theme.colores["card"],
                    fg=self.theme.colores["texto"],
                    font=("Segoe UI", 10, "bold"),
                    width=20,
                    anchor="w").pack(side="left", padx=(0, 5))
            
            # Entry para mostrar la ruta
            ruta_var = tk.StringVar(value=self.sonidos_configurados.get(nombre, ""))
            entry = tk.Entry(frame,
                           textvariable=ruta_var,
                           width=35,
                           bg=self.theme.colores.get("superficie3", "#2d3047"),
                           fg=self.theme.colores["texto"],
                           relief="flat",
                           font=("Segoe UI", 9))
            entry.pack(side="left", padx=5)
            
            # Botón para seleccionar archivo
            tk.Button(frame,
                     text="📂 Seleccionar",
                     bg=self.theme.colores["accento"],
                     fg=self.theme.colores["texto"],
                     font=("Segoe UI", 9),
                     relief="flat",
                     padx=8,
                     pady=2,
                     cursor="hand2",
                     command=lambda t=nombre, var=ruta_var: self._seleccionar_sonido(t, var)).pack(side="left", padx=2)
            
            # Botón para probar sonido
            tk.Button(frame,
                     text="🔊 Probar",
                     bg=self.theme.colores["success"],
                     fg=self.theme.colores["texto"],
                     font=("Segoe UI", 9),
                     relief="flat",
                     padx=8,
                     pady=2,
                     cursor="hand2",
                     command=lambda var=ruta_var: self._probar_sonido(var.get())).pack(side="left", padx=2)
            
            self.sonido_vars[nombre] = ruta_var
        
        # Botón para guardar configuraciones de sonido
        tk.Button(card,
                 text="💾 Guardar Configuración de Sonidos",
                 bg=self.theme.colores["success"],
                 fg=self.theme.colores["texto"],
                 font=("Segoe UI", 10, "bold"),
                 relief="flat",
                 padx=15,
                 pady=8,
                 cursor="hand2",
                 command=self._guardar_sonidos).pack(pady=(10, 15))
    
    def _seleccionar_sonido(self, tipo_falla, var):
        """Abre un diálogo para seleccionar un archivo de sonido"""
        file_path = filedialog.askopenfilename(
            title=f"Seleccionar sonido para {tipo_falla}",
            filetypes=[
                ("Archivos de audio", "*.mp3 *.wav"),
                ("MP3 files", "*.mp3"),
                ("WAV files", "*.wav"),
                ("Todos los archivos", "*.*")
            ]
        )
        if file_path:
            var.set(file_path)
            # Opcional: probar el sonido inmediatamente
            self._probar_sonido(file_path)
    
    def _probar_sonido(self, file_path):
        """Prueba la reproducción de un sonido"""
        if file_path and self.controller.sound_service:
            self.controller.sound_service.play_sound(file_path)
    
    def _guardar_sonidos(self):
        """Guarda las configuraciones de sonido en la BD"""
        for tipo, var in self.sonido_vars.items():
            ruta = var.get().strip()
            if ruta:
                # Validar que el archivo existe
                if not os.path.exists(ruta):
                    messagebox.showwarning("Archivo no encontrado", 
                                          f"El archivo para '{tipo}' no existe: {ruta}")
                    continue
                self.falla_controller.sound_model.guardar_sonido(tipo, ruta)
            else:
                # Si la ruta está vacía, eliminar la configuración
                self.falla_controller.sound_model.eliminar_sonido(tipo)
        
        # Recargar los sonidos en el controlador
        self.falla_controller.sonidos_configurados = self.falla_controller.sound_model.cargar_sonidos()
        messagebox.showinfo("Configuración Guardada", "Sonidos de alarma actualizados correctamente.")