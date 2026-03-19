# instalador.py

import tkinter as tk
from tkinter import messagebox, ttk, colorchooser  
import hashlib
import sys
import os
from datetime import datetime
import mysql.connector

# Importar desde la nueva estructura
from src.models.database import Database
from src.models.config_model import ConfigModel
from src.models.falla_model import FallaModel
from src.models.licencia_model import LicenciaModel
from src.utils.constants import DB_CONFIG_DEFAULT

# Importar función de creación de tablas
from instalador_bd import crear_tablas_mysql

class InstaladorAndon:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Instalación - Sistema Andon")
        self.root.geometry("600x700")
        self.root.configure(bg="#1a1a2e")
        
        # Generar ID de instalación
        computer_name = os.environ.get('COMPUTERNAME', 'unknown')
        self.installation_id = hashlib.md5(computer_name.encode()).hexdigest()[:12].upper()
        
        # Configuraciones
        self.config_licencia = None
        self.config_db = None
        self.mysql_vars = {}
        
        # Datos de instalación
        self.tipos_instalacion = []
        self.tipos_falla_instalacion = []
        self.mapeo_instalacion = {}
        self.mapeo_vars_instalacion = {}
        self.mapeo_labels = {}
        
        # Iniciar asistente
        self.root.after(100, self.paso1_activacion_licencia)
        self.root.mainloop()
    
    # ========== PASO 1: ACTIVACIÓN DE LICENCIA ==========
    def paso1_activacion_licencia(self):
        """Pantalla de activación de licencia"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Título
        tk.Label(self.root, text="🔐 ACTIVACIÓN DE LICENCIA", 
                bg="#1a1a2e", fg="white", font=("Segoe UI", 20, "bold")).pack(pady=40)
        
        # ID de instalación
        tk.Label(self.root, text="ID de Instalación:", 
                bg="#1a1a2e", fg="#b0b0b0", font=("Segoe UI", 11)).pack(pady=(10, 0))
        
        id_frame = tk.Frame(self.root, bg="#16213e")
        id_frame.pack(pady=5)
        
        tk.Label(id_frame, text=self.installation_id, 
                bg="#0f3460", fg="#e94560", font=("Consolas", 12, "bold"),
                padx=15, pady=5).pack()
        
        # Frame principal para opciones
        opciones_frame = tk.Frame(self.root, bg="#1a1a2e")
        opciones_frame.pack(expand=True, fill="both", padx=30, pady=20)
        
        # Opción 1: Activar licencia
        licencia_card = tk.Frame(opciones_frame, bg="#16213e", relief="flat", bd=2)
        licencia_card.pack(fill="x", pady=10)
        
        tk.Label(licencia_card, text="🔑 ACTIVAR LICENCIA EXISTENTE",
                bg="#16213e", fg="white", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=20, pady=(15, 5))
        
        tk.Label(licencia_card, text="Ingresa tu clave de licencia:",
                bg="#16213e", fg="#b0b0b0", font=("Segoe UI", 10)).pack(anchor="w", padx=20, pady=5)
        
        entry_frame = tk.Frame(licencia_card, bg="#16213e")
        entry_frame.pack(fill="x", padx=20, pady=10)
        
        self.entry_licencia = tk.Entry(entry_frame, width=30, bg="#0f3460", fg="white",
                                      font=("Segoe UI", 11), relief="flat")
        self.entry_licencia.pack(side="left", padx=(0, 10))
        
        tk.Button(entry_frame, text="Validar", 
                 command=self.validar_licencia_ingresada,
                 bg="#2196F3", fg="white", font=("Segoe UI", 9, "bold"),
                 relief="flat", padx=15, pady=5, cursor="hand2").pack(side="left")
        
        # Separador
        tk.Frame(opciones_frame, bg="#b0b0b0", height=1).pack(fill="x", pady=20)
        
        # Opción 2: Iniciar demo
        demo_card = tk.Frame(opciones_frame, bg="#16213e", relief="flat", bd=2)
        demo_card.pack(fill="x", pady=10)
        
        tk.Label(demo_card, text="🎁 PERIODO DE DEMO (15 DÍAS)",
                bg="#16213e", fg="white", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=20, pady=(15, 5))
        
        tk.Label(demo_card, text="Prueba el sistema completo por 15 días",
                bg="#16213e", fg="#b0b0b0", font=("Segoe UI", 10)).pack(anchor="w", padx=20, pady=5)
        
        tk.Label(demo_card, text="✓ Acceso a todas las funciones PRO\n✓ Sin costo\n✓ 15 días de prueba",
                bg="#16213e", fg="#b0b0b0", font=("Segoe UI", 9), justify="left").pack(anchor="w", padx=20, pady=5)
        
        tk.Button(demo_card, text="INICIAR DEMO GRATUITA", 
                 command=self.iniciar_demo_desde_instalador,
                 bg="#FFC107", fg="black", font=("Segoe UI", 11, "bold"),
                 relief="flat", padx=20, pady=10, cursor="hand2").pack(pady=15)
        
        # Mensaje informativo
        tk.Label(self.root, 
                text="⚠️ Se requiere una licencia válida o demo para usar el sistema",
                bg="#1a1a2e", fg="#FF5252", font=("Segoe UI", 9, "italic")).pack(side="bottom", pady=10)
        
        self.root.update_idletasks()
        self.entry_licencia.focus()
    
    def validar_licencia_ingresada(self):
        """Valida la licencia ingresada usando el modelo"""
        license_key = self.entry_licencia.get().strip()
        if not license_key:
            messagebox.showerror("Error", "Por favor ingresa una clave de licencia")
            return
        
        # Crear modelo de licencia temporal
        db_temp = Database()
        licencia_model = LicenciaModel(db_temp)
        
        print(f"🔍 Validando licencia: {license_key}")
        valido, info = licencia_model.validar_licencia_online(license_key, self.installation_id)
        
        if valido:
            self.config_licencia = {
                "installation_id": self.installation_id,
                "license_key": license_key,
                "license_type": info['license_type'],
                "demo_used": False,
                "demo_start": "",
                "demo_expires": "",
                "max_fallas": info['max_fallas'],
                "max_maquinas": info['max_maquinas'],
                "last_validation": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "grace_period_start": "",
                "excel_exports_today": 0,
                "last_export_date": "",
                "expires_at": info['expires_at']
            }
            messagebox.showinfo("✅ Licencia Válida", 
                              f"Licencia {info['license_type'].upper()} activada correctamente")
            self.paso2_seleccion_bd()
        else:
            messagebox.showerror("❌ Licencia Inválida", f"No se pudo validar la licencia:\n{info}")
    
    def iniciar_demo_desde_instalador(self):
        """Inicia periodo de demo usando el modelo"""
        db_temp = Database()
        licencia_model = LicenciaModel(db_temp)
        
        exito, info = licencia_model.iniciar_demo(self.installation_id)
        
        if exito:
            self.config_licencia = {
                "installation_id": self.installation_id,
                "license_key": "",
                "license_type": "demo",
                "demo_used": True,
                "demo_start": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "demo_expires": info,
                "max_fallas": 5,
                "max_maquinas": 200,
                "last_validation": "",
                "grace_period_start": "",
                "excel_exports_today": 0,
                "last_export_date": "",
                "expires_at": info
            }
            messagebox.showinfo("🎁 Demo Activado", 
                              f"Periodo de demo de 15 días activado\nVálido hasta: {info}\n\n"
                              "Tendrás acceso a todas las funciones PRO durante este periodo.")
            self.paso2_seleccion_bd()
        else:
            messagebox.showerror("❌ Error", f"No se pudo iniciar demo:\n{info}")
    
    # ========== PASO 2: CONFIGURACIÓN DE BASE DE DATOS ==========
    def paso2_seleccion_bd(self):
        """Configuración de la base de datos MySQL"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        tipo_licencia = self.config_licencia['license_type']
        
        tk.Label(self.root, text="💾 CONFIGURACIÓN DE BASE DE DATOS", 
                bg="#1a1a2e", fg="white", font=("Segoe UI", 20, "bold")).pack(pady=40)
        
        # Mostrar info de licencia
        if tipo_licencia == 'demo':
            info_text = f"🎁 MODO DEMO - Válido hasta: {self.config_licencia['demo_expires']}"
            info_color = "#FFC107"
        else:
            info_text = f"🔑 Licencia: {tipo_licencia.upper()} | Máquinas: {self.config_licencia['max_maquinas']} | Fallas: {self.config_licencia['max_fallas']}"
            info_color = "#e94560"
        
        tk.Label(self.root, text=info_text, bg="#16213e", fg=info_color, 
                font=("Segoe UI", 10, "bold")).pack(pady=10)
        
        # Mensaje informativo
        tk.Label(self.root, 
                text="El sistema requiere una base de datos MySQL.\nIngresa los datos de conexión a tu servidor MySQL.",
                bg="#1a1a2e", fg="white", font=("Segoe UI", 11)).pack(pady=20)
        
        # Formulario MySQL
        self.mysql_frame = tk.Frame(self.root, bg="#16213e")
        self.mysql_frame.pack(fill="x", padx=20, pady=20)
        
        campos_mysql = [
            ("Host:", "localhost"),
            ("Puerto:", "3306"),
            ("Usuario:", "root"),
            ("Contraseña:", ""),
            ("Base de Datos:", "andon_db"),
        ]
        
        for i, (label, default) in enumerate(campos_mysql):
            f = tk.Frame(self.mysql_frame, bg="#16213e")
            f.pack(fill="x", padx=20, pady=2)
            tk.Label(f, text=label, bg="#16213e", fg="white", width=15, anchor="w").pack(side="left")
            var = tk.StringVar(value=default)
            entry = tk.Entry(f, textvariable=var, bg="#0f3460", fg="white", relief="flat")
            if "Contraseña" in label:
                entry.config(show="*")
            entry.pack(side="left", fill="x", expand=True)
            self.mysql_vars[label] = var
        
        # Opciones SSL y Timeout
        opciones_frame = tk.Frame(self.mysql_frame, bg="#16213e")
        opciones_frame.pack(fill="x", padx=20, pady=10)
        
        self.ssl_var = tk.BooleanVar(value=False)
        tk.Checkbutton(opciones_frame, text="Usar SSL", variable=self.ssl_var,
                      bg="#16213e", fg="white", selectcolor="#0f3460").pack(anchor="w")
        
        timeout_frame = tk.Frame(opciones_frame, bg="#16213e")
        timeout_frame.pack(fill="x", pady=5)
        tk.Label(timeout_frame, text="Timeout (seg):", bg="#16213e", fg="white", 
                width=15, anchor="w").pack(side="left")
        self.timeout_var = tk.StringVar(value="30")
        tk.Entry(timeout_frame, textvariable=self.timeout_var, bg="#0f3460", 
                fg="white", width=10, relief="flat").pack(side="left")
        
        # Botón para probar conexión
        tk.Button(self.mysql_frame, text="🔌 Probar Conexión", 
                 command=self.probar_conexion_mysql,
                 bg="#2196F3", fg="white", font=("Segoe UI", 9, "bold"),
                 relief="flat", padx=15, pady=5, cursor="hand2").pack(pady=10)
        
        # Botón de continuar
        tk.Button(self.root, text="▶ CONTINUAR", 
                 command=self.paso2_5_personalizar_fallas,
                 bg="#4CAF50", fg="white", font=("Segoe UI", 12, "bold"), 
                 padx=30, pady=10, cursor="hand2").pack(pady=30)
    
    def probar_conexion_mysql(self):
        """Prueba la conexión a MySQL"""
        try:
            config = {
                "host": self.mysql_vars["Host:"].get(),
                "port": int(self.mysql_vars["Puerto:"].get()),
                "usuario": self.mysql_vars["Usuario:"].get(),
                "password": self.mysql_vars["Contraseña:"].get(),
                "base_datos": self.mysql_vars["Base de Datos:"].get(),
                "timeout": int(self.timeout_var.get()),
                "usar_ssl": self.ssl_var.get()
            }
            
            db_temp = Database()
            db_temp.initialize(config)
            exito, msg = db_temp.test_connection()
            
            if exito:
                messagebox.showinfo("✅ Éxito", f"Conexión exitosa:\n{msg}")
            else:
                messagebox.showerror("❌ Error", f"No se pudo conectar:\n{msg}")
        except Exception as e:
            messagebox.showerror("❌ Error", f"Error al probar conexión:\n{str(e)}")
    
    # ========== PASO 2.5: PERSONALIZAR FALLAS ==========
    def paso2_5_personalizar_fallas(self):
        """Paso de personalización de tipos de falla (disponible para TODAS las licencias durante instalación)"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        tipo_licencia = self.config_licencia['license_type']
        
        tk.Label(self.root, text="🎨 PERSONALIZAR TIPOS DE FALLA", 
                bg="#1a1a2e", fg="white", font=("Segoe UI", 20, "bold")).pack(pady=40)
        
        # Mostrar info de licencia y límites
        info_text = f"🔑 Licencia: {tipo_licencia.upper()} | Tipos máximos: {self.config_licencia['max_fallas']}"
        info_color = "#e94560" if tipo_licencia != 'demo' else "#FFC107"
        
        tk.Label(self.root, text=info_text, bg="#16213e", fg=info_color, 
                font=("Segoe UI", 11, "bold")).pack(pady=10)
        
        # Frame principal con scroll
        canvas_frame = tk.Frame(self.root, bg="#1a1a2e")
        canvas_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        canvas = tk.Canvas(canvas_frame, bg="#1a1a2e", highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#1a1a2e")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=canvas.winfo_width())
        
        def configure_frame_width(event):
            canvas.itemconfig(1, width=event.width)
        
        canvas.bind('<Configure>', configure_frame_width)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # ===== TIPOS DE FALLA =====
        tipos_card = tk.Frame(scrollable_frame, bg="#16213e", relief="flat", bd=2)
        tipos_card.pack(fill="x", pady=(0, 20))
        
        # Header con título y botón de actualizar
        tipos_header = tk.Frame(tipos_card, bg="#16213e")
        tipos_header.pack(fill="x", padx=20, pady=(15, 10))
        
        tk.Label(tipos_header, text="📊 TIPOS DE FALLA", 
                bg="#16213e", fg="white", font=("Segoe UI", 14, "bold")).pack(side="left")
        
        # Botón para actualizar lista de botones
        tk.Button(tipos_header, text="🔄 Actualizar Lista de Botones", 
                command=self._actualizar_lista_botones,
                bg="#2196F3", fg="white", font=("Segoe UI", 9, "bold"),
                relief="flat", padx=10, pady=3, cursor="hand2").pack(side="right")
        
        tk.Label(tipos_card, text=f"Configura hasta {self.config_licencia['max_fallas']} tipos de falla:", 
                bg="#16213e", fg="#b0b0b0", font=("Segoe UI", 10)).pack(anchor="w", padx=20, pady=(0, 10))
        
        # Frame para la lista de tipos
        self.tipos_list_frame = tk.Frame(tipos_card, bg="#16213e")
        self.tipos_list_frame.pack(fill="x", padx=20, pady=5)
        
        # Variables para guardar los tipos
        self.tipos_instalacion = []
        
        # Valores por defecto
        tipos_default = ["Mantenimiento", "Producción", "Calidad", "Materiales", "Ingeniería"]
        colores_default = ["#FF9A00", "#FF5252", "#4CAF50", "#2196F3", "#9C27B0"]
        
        # Crear filas para cada tipo (hasta el límite de la licencia)
        max_tipos = self.config_licencia['max_fallas']
        for i in range(max_tipos):
            self._crear_fila_tipo_falla(tipos_card, i, 
                                        tipos_default[i] if i < len(tipos_default) else f"Tipo {i+1}", 
                                        colores_default[i] if i < len(colores_default) else "#e94560")
        
        # ===== MAPEO DE BOTONES =====
        mapeo_card = tk.Frame(scrollable_frame, bg="#16213e", relief="flat", bd=2)
        mapeo_card.pack(fill="x", pady=(0, 20))
        
        tk.Label(mapeo_card, text="🔌 ASIGNACIÓN DE BOTONES", 
                bg="#16213e", fg="white", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=20, pady=(15, 10))
        
        tk.Label(mapeo_card, text="Asigna cada botón físico a un tipo de falla (opcional):", 
                bg="#16213e", fg="#b0b0b0", font=("Segoe UI", 10)).pack(anchor="w", padx=20, pady=(0, 10))
        
        tk.Label(mapeo_card, 
                text=f"Nota: Tu licencia permite hasta {self.config_licencia['max_fallas']} tipos de falla.",
                bg="#16213e", fg="#FFC107", font=("Segoe UI", 9, "italic")).pack(anchor="w", padx=20, pady=(0, 5))
        
        tk.Label(mapeo_card, 
                text="Los botones adicionales no estarán disponibles.",
                bg="#16213e", fg="#b0b0b0", font=("Segoe UI", 9)).pack(anchor="w", padx=20, pady=(0, 10))
        
        # Frame para mapeo
        self.mapeo_frame = tk.Frame(mapeo_card, bg="#16213e")
        self.mapeo_frame.pack(fill="x", padx=20, pady=5)
        
        # Variables para guardar mapeo
        self.mapeo_vars_instalacion = {}
        self.mapeo_labels = {}
        
        # Crear filas para botones
        self._crear_todos_botones()
        
        # ===== BOTONES DE ACCIÓN =====
        btn_frame = tk.Frame(scrollable_frame, bg="#1a1a2e")
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="⏪ VOLVER", 
                command=self.paso2_seleccion_bd,
                bg="#FF5252", fg="white", font=("Segoe UI", 11), 
                padx=30, pady=8, cursor="hand2").pack(side="left", padx=10)
        
        tk.Button(btn_frame, text="▶ CONTINUAR", 
                command=self.paso3_confirmar_instalacion,
                bg="#4CAF50", fg="white", font=("Segoe UI", 12, "bold"), 
                padx=30, pady=8, cursor="hand2").pack(side="left", padx=10)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _actualizar_lista_botones(self):
        """Actualiza la lista de botones con los nombres actuales de tipos"""
        try:
            # Obtener lista actualizada de tipos
            tipos_actualizados = []
            for tipo_data in self.tipos_instalacion:
                nombre = tipo_data["var"].get().strip()
                if nombre:
                    tipos_actualizados.append(nombre)
            
            # Recrear todos los botones
            self._crear_todos_botones()
            
            # Mostrar mensaje de confirmación
            messagebox.showinfo("✅ Actualizado", 
                            f"Lista de botones actualizada con {len(tipos_actualizados)} tipos.\n"
                            "Ahora puedes asignar los botones.")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar la lista:\n{str(e)}")
    
    def _crear_fila_tipo_falla(self, parent, index, nombre_default, color_default):
        """Crea una fila para configurar un tipo de falla"""
        frame = tk.Frame(parent, bg="#16213e")
        frame.pack(fill="x", pady=3, padx=20)
        
        # Número
        tk.Label(frame, text=f"{index+1}.", bg="#16213e", fg="#b0b0b0", 
                font=("Segoe UI", 10), width=2).pack(side="left")
        
        # Nombre
        var_nombre = tk.StringVar(value=nombre_default)
        entry = tk.Entry(frame, textvariable=var_nombre, bg="#0f3460", fg="white",
                        font=("Segoe UI", 10), width=20, relief="flat")
        entry.pack(side="left", padx=5)
        
        # Color
        var_color = tk.StringVar(value=color_default)
        color_frame = tk.Frame(frame, bg=var_color.get(), width=50, height=20)
        color_frame.pack(side="left", padx=5)
        color_frame.pack_propagate(False)
        
        color_label = tk.Label(color_frame, text="Color", bg=var_color.get(), 
                            fg="white" if self._is_dark_color(color_default) else "black",
                            font=("Segoe UI", 8))
        color_label.pack(expand=True, fill="both")
        
        # Botón para cambiar color
        def cambiar_color(v=var_color, l=color_label, cf=color_frame):
            color = colorchooser.askcolor(title=f"Color para Tipo {index+1}", initialcolor=v.get())
            if color and color[1]:
                v.set(color[1])
                cf.config(bg=color[1])
                l.config(bg=color[1], fg="white" if self._is_dark_color(color[1]) else "black")
        
        tk.Button(frame, text="🎨", bg="#2196F3", fg="white", font=("Segoe UI", 8, "bold"),
                relief="flat", width=3, cursor="hand2",
                command=cambiar_color).pack(side="left", padx=2)
        
        # Guardar referencias
        self.tipos_instalacion.append({"var": var_nombre, "color_var": var_color, "entry": entry})
    
    def _crear_todos_botones(self):
        """Crea o recrea todos los botones de asignación"""
        # Limpiar frame de botones
        for widget in self.mapeo_frame.winfo_children():
            widget.destroy()
        
        self.mapeo_vars_instalacion.clear()
        self.mapeo_labels.clear()
        
        # Obtener lista actual de tipos
        tipos_actualizados = []
        for tipo_data in self.tipos_instalacion:
            nombre = tipo_data["var"].get().strip()
            if nombre:
                tipos_actualizados.append(nombre)
        
        # Crear botones (siempre 5, pero algunos pueden estar deshabilitados)
        for i in range(1, 6):
            self._crear_fila_mapeo_boton(self.mapeo_frame, i, tipos_actualizados)
    
    def _crear_fila_mapeo_boton(self, parent, numero_boton, tipos_disponibles):
        """Crea una fila para asignar un botón a un tipo de falla"""
        frame = tk.Frame(parent, bg="#16213e")
        frame.pack(fill="x", pady=3, padx=20)
        
        tk.Label(frame, text=f"Botón {numero_boton}:", bg="#16213e", fg="white",
                font=("Segoe UI", 10, "bold"), width=10, anchor="w").pack(side="left")
        
        # Si el botón excede el límite de tipos de la licencia
        if numero_boton > self.config_licencia['max_fallas']:
            label = tk.Label(frame, text="⚠️ Fuera de límite de licencia", 
                            bg="#16213e", fg="#FF5252", font=("Segoe UI", 9, "italic"))
            label.pack(side="left", padx=5)
            self.mapeo_labels[numero_boton] = label
            return
        
        # Si no hay suficientes tipos configurados para este botón
        if numero_boton > len(tipos_disponibles):
            label = tk.Label(frame, text="❌ Sin tipo disponible (actualiza lista)", 
                            bg="#16213e", fg="#FFA500", font=("Segoe UI", 9, "italic"))
            label.pack(side="left", padx=5)
            self.mapeo_labels[numero_boton] = label
            return
        
        # Botón disponible - crear combobox
        var = tk.StringVar()
        combo = ttk.Combobox(frame, textvariable=var, values=tipos_disponibles,
                            width=25, state="readonly")
        combo.pack(side="left", padx=5)
        
        # Asignar tipo por defecto (el correspondiente al número de botón)
        if numero_boton <= len(tipos_disponibles):
            var.set(tipos_disponibles[numero_boton - 1])
        
        self.mapeo_vars_instalacion[numero_boton] = var
    
    def _is_dark_color(self, hex_color):
        """Determina si un color es oscuro para elegir texto blanco o negro"""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return luminance < 0.5
    
    # ========== PASO 3: CONFIRMACIÓN E INSTALACIÓN ==========
    def paso3_confirmar_instalacion(self):
        """Confirma e instala el sistema"""
        # Recolectar tipos de falla configurados
        self.tipos_falla_instalacion = []
        for tipo_data in self.tipos_instalacion:
            nombre = tipo_data["var"].get().strip()
            if nombre:  # Solo incluir si tiene nombre
                color = tipo_data["color_var"].get()
                self.tipos_falla_instalacion.append({
                    "nombre": nombre,
                    "color": color
                })
        
        # Si no hay ninguno, usar valores por defecto
        if not self.tipos_falla_instalacion:
            tipos_default = ["Mantenimiento", "Producción", "Calidad"]
            colores_default = ["#FF9A00", "#FF5252", "#4CAF50"]
            max_tipos = self.config_licencia['max_fallas']
            for i in range(min(len(tipos_default), max_tipos)):
                self.tipos_falla_instalacion.append({
                    "nombre": tipos_default[i],
                    "color": colores_default[i]
                })
        
        # Recolectar mapeo de botones
        self.mapeo_instalacion = {}
        for num_boton, var in self.mapeo_vars_instalacion.items():
            if num_boton <= self.config_licencia['max_fallas']:  # Solo dentro del límite
                tipo = var.get().strip()
                if tipo:  # Solo guardar si seleccionó algo
                    self.mapeo_instalacion[num_boton] = tipo
        
        # Limpiar la ventana para mostrar el resumen
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Preparar configuración de BD
        try:
            self.config_db = {
                "tipo": "mysql",
                "host": self.mysql_vars["Host:"].get(),
                "port": int(self.mysql_vars["Puerto:"].get()),
                "usuario": self.mysql_vars["Usuario:"].get(),
                "password": self.mysql_vars["Contraseña:"].get(),
                "base_datos": self.mysql_vars["Base de Datos:"].get(),
                "timeout": int(self.timeout_var.get()),
                "usar_ssl": self.ssl_var.get()
            }
        except KeyError as e:
            messagebox.showerror("Error", f"Falta configuración: {e}")
            self.paso2_seleccion_bd()
            return
        
        db_info = f"MySQL: {self.config_db['host']}/{self.config_db['base_datos']}"
        
        tk.Label(self.root, text="⚙️ CONFIRMAR INSTALACIÓN", 
                bg="#1a1a2e", fg="white", font=("Segoe UI", 20, "bold")).pack(pady=40)
        
        # Determinar tipo de licencia para el resumen
        if self.config_licencia['license_type'] == 'demo':
            tipo_licencia_texto = f"🎁 DEMO (expira: {self.config_licencia['demo_expires']})"
        else:
            tipo_licencia_texto = f"🔑 {self.config_licencia['license_type'].upper()}"
        
        # Crear el texto de los tipos configurados
        tipos_texto = "\n".join([f"    • {t['nombre']}" for t in self.tipos_falla_instalacion[:5]])
        
        # Resumen
        resumen = f"""
    📋 RESUMEN DE CONFIGURACIÓN:

    🆔 ID Instalación: {self.installation_id}
    🔑 Licencia: {tipo_licencia_texto}
    🔧 Máquinas permitidas: {self.config_licencia['max_maquinas']}

    📊 TIPOS DE FALLA CONFIGURADOS:
    {tipos_texto}

    🔌 Mapeo de botones: {len(self.mapeo_instalacion)} asignaciones

    💾 Base de datos: {db_info}

    ⚠️ Al continuar, se guardará toda la configuración.
    """
        
        tk.Label(self.root, text=resumen, bg="#16213e", fg="white", 
                font=("Segoe UI", 11), justify="left", padx=30, pady=20).pack(pady=20)
        
        # Botones
        btn_frame = tk.Frame(self.root, bg="#1a1a2e")
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="✅ CONFIRMAR E INSTALAR", 
                command=self.ejecutar_instalacion,
                bg="#4CAF50", fg="white", font=("Segoe UI", 12, "bold"), 
                padx=30, pady=10, cursor="hand2").pack(pady=10)
        
        tk.Button(btn_frame, text="↻ VOLVER", 
                command=self.paso2_5_personalizar_fallas,  # Volver a personalización
                bg="#FF5252", fg="white", font=("Segoe UI", 11), 
                padx=20, pady=5, cursor="hand2").pack(pady=5)
    
    def ejecutar_instalacion(self):
        """Ejecuta la instalación usando los nuevos modelos"""
        try:
            print("\n" + "="*50)
            print("INICIANDO INSTALACIÓN")
            print("="*50 + "\n")
            
            # 1. Probar conexión antes de instalar
            print("[1/7] Probando conexión a MySQL...")
            print(f"    Host: {self.config_db['host']}")
            print(f"    Puerto: {self.config_db['port']}")
            print(f"    Usuario: {self.config_db['usuario']}")
            print(f"    Base de datos: {self.config_db['base_datos']}")
            
            db = Database()
            db.initialize(self.config_db)
            exito, msg = db.test_connection()
            
            if not exito:
                print(f"    ❌ Error: {msg}")
                messagebox.showerror("Error de Conexión", 
                                f"No se puede conectar a MySQL:\n{msg}\n\n"
                                "Verifica:\n"
                                "• Que MySQL esté instalado y corriendo\n"
                                "• Los datos de conexión\n"
                                "• Que la contraseña sea correcta")
                return
            print("    ✅ Conexión exitosa")
            
            # 2. Verificar/Crear base de datos
            print("\n[2/7] Verificando base de datos...")
            try:
                import mysql.connector
                # Primero, intentar conectar directamente a la base de datos
                print(f"    Verificando si la base de datos '{self.config_db['base_datos']}' existe...")
                try:
                    conn = mysql.connector.connect(
                        host=self.config_db["host"],
                        port=self.config_db["port"],
                        user=self.config_db["usuario"],
                        password=self.config_db["password"],
                        database=self.config_db["base_datos"],
                        connection_timeout=self.config_db["timeout"],
                        ssl_disabled=not self.config_db["usar_ssl"],
                        use_pure=True
                    )
                    conn.close()
                    print(f"    ✅ La base de datos '{self.config_db['base_datos']}' YA EXISTE y es accesible")
                    
                except mysql.connector.Error as e:
                    if "1049" in str(e):
                        print(f"    ⚠️ La base de datos no existe. Intentando crearla...")
                        
                        conn = mysql.connector.connect(
                            host=self.config_db["host"],
                            port=self.config_db["port"],
                            user=self.config_db["usuario"],
                            password=self.config_db["password"],
                            connection_timeout=self.config_db["timeout"],
                            ssl_disabled=not self.config_db["usar_ssl"],
                            use_pure=True
                        )
                        cursor = conn.cursor()
                        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.config_db['base_datos']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                        conn.close()
                        print(f"    ✅ Base de datos creada correctamente")
                    else:
                        print(f"    ❌ Error al conectar: {e}")
                        raise Exception(f"Error conectando a MySQL: {str(e)}")
                        
            except Exception as e:
                print(f"    ❌ Error MySQL: {e}")
                raise Exception(f"Error con MySQL: {str(e)}")
            
            # 3. Crear tablas en MySQL
            print("\n[3/7] Creando tablas...")
            try:
                exito, msg = crear_tablas_mysql(self.config_db)
                if not exito:
                    print(f"    ❌ Error: {msg}")
                    raise Exception(f"Error creando tablas:\n{msg}")
                print("    ✅ Tablas creadas correctamente")
            except Exception as e:
                print(f"    ❌ Excepción: {str(e)}")
                import traceback
                traceback.print_exc()
                raise
            
            # 4. Guardar configuración de licencia
            print("\n[4/7] Guardando licencia...")
            try:
                licencia_model = LicenciaModel(db)
                licencia_model.guardar_config_licencia(self.config_licencia)
                print("    ✅ Licencia guardada")
            except Exception as e:
                print(f"    ❌ Error: {str(e)}")
                raise
            
            # 5. Guardar configuración de BD
            print("\n[5/7] Guardando configuración...")
            try:
                ConfigModel.guardar_config_db(self.config_db)
                print("    ✅ Configuración guardada")
            except Exception as e:
                print(f"    ❌ Error: {str(e)}")
                raise
            
            # 6. Guardar tipos de falla por defecto
            print("\n[6/7] Guardando tipos de falla...")
            try:
                if self.tipos_falla_instalacion:
                    falla_model = FallaModel(db)
                    falla_model.guardar_tipos_falla(self.tipos_falla_instalacion)
                    print(f"    ✅ {len(self.tipos_falla_instalacion)} tipos de falla guardados")
            except Exception as e:
                print(f"    ❌ Error: {str(e)}")
                raise
            
            # 7. Guardar configuración del sistema
            print("\n[7/7] Guardando configuración del sistema...")
            try:
                config_sistema_default = {
                    "nombre_sistema": "ANDON SYSTEM",
                    "tema_activo": "oscuro",
                    "color_fondo": "#1a1a2e",
                    "color_sidebar": "#16213e",
                    "color_card": "#0f3460",
                    "superficie3": "#2d3047",
                    "color_texto": "#ffffff",
                    "texto_principal": "#ffffff",
                    "color_texto_secundario": "#b0b0b0",
                    "texto_secundario": "#b0b0b0",
                    "color_acento": "#e94560",
                    "acento_principal": "#e94560",
                    "color_exito": "#00C853",
                    "exito": "#00C853",
                    "color_warning": "#FFC107",
                    "advertencia": "#FFC107",
                    "color_danger": "#FF5252",
                    "peligro": "#FF5252",
                    "color_pendiente": "#FFA500",
                    "pendiente": "#FFA500"
                }
                config_model = ConfigModel(db)
                config_model.guardar_config_sistema(config_sistema_default)
                print("    ✅ Configuración del sistema guardada")
            except Exception as e:
                print(f"    ❌ Error: {str(e)}")
                raise
            
            # 8. Guardar mapeo de botones (si existe)
            if hasattr(self, 'mapeo_instalacion') and self.mapeo_instalacion:
                print("\n[8/8] Guardando mapeo de botones...")
                try:
                    falla_model = FallaModel(db)
                    falla_model.guardar_mapeo_botones(self.mapeo_instalacion)
                    print(f"    ✅ {len(self.mapeo_instalacion)} asignaciones guardadas")
                except Exception as e:
                    print(f"    ❌ Error: {str(e)}")
                    # No raise, es opcional
            else:
                print("\n[8/8] Sin mapeo de botones para guardar")
            
            print("\n" + "="*50)
            print("✅ INSTALACIÓN COMPLETADA EXITOSAMENTE")
            print("="*50 + "\n")
            
            messagebox.showinfo("✅ INSTALACIÓN COMPLETADA", 
                            "El sistema se ha instalado correctamente.\n\nLa aplicación se iniciará ahora.")
            
            self.root.destroy()
            self.iniciar_aplicacion()
            
        except mysql.connector.Error as e:
            error_msg = str(e)
            print(f"\n❌ ERROR MySQL: {error_msg}")
            import traceback
            traceback.print_exc()
            
            if "1045" in error_msg:
                user_msg = "Usuario o contraseña incorrectos para MySQL"
            elif "1049" in error_msg:
                user_msg = "La base de datos no existe y no se pudo crear"
            elif "2003" in error_msg:
                user_msg = "No se pudo conectar al servidor MySQL.\n¿Está instalado y corriendo?"
            else:
                user_msg = f"Error de MySQL: {error_msg}"
            
            messagebox.showerror("❌ ERROR DE INSTALACIÓN", 
                            f"Ocurrió un error en MySQL:\n\n{user_msg}\n\n"
                            "Verifica la instalación de MySQL e intenta de nuevo.\n\n"
                            "Revisa la consola para más detalles.")
            
        except Exception as e:
            print(f"\n❌ ERROR GENERAL: {str(e)}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("❌ ERROR DE INSTALACIÓN", 
                            f"Ocurrió un error inesperado:\n\n{str(e)}\n\n"
                            "Revisa la consola para más detalles.")
    
    def iniciar_aplicacion(self):
        """Inicia la aplicación principal"""
        try:
            from src.main import main
            main()
        except Exception as e:
            print(f"❌ Error al iniciar aplicación: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error Crítico", 
                                f"No se pudo iniciar la aplicación:\n{str(e)}")

if __name__ == "__main__":
    # Verificar si ya está instalado
    if os.path.exists("db_config.json"):
        # Ya instalado, iniciar directamente la app
        try:
            from src.main import main
            main()
        except Exception as e:
            print(f"❌ Error al iniciar aplicación: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error Crítico", 
                                f"No se pudo iniciar la aplicación:\n{str(e)}")
    else:
        # No instalado, ejecutar instalador
        InstaladorAndon()