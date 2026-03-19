# src/views/proyeccion_view.py

import tkinter as tk
from tkinter import ttk
from datetime import datetime
from src.utils.helpers import solo_hora, is_light_color
import logging

logger = logging.getLogger(__name__)

class ProyeccionView:
    """Ventana de proyección para mostrar fallas en pantalla completa"""
    
    def __init__(self, parent, controller, theme_service, falla_controller):
        self.parent = parent
        self.controller = controller
        self.theme = theme_service
        self.falla_controller = falla_controller
        
        # Configuración de proyección
        self.config = controller.config_proyeccion
        
        # Crear ventana
        self.ventana = tk.Toplevel(parent)
        self.ventana.title(f"{self.theme.colores.get('nombre_sistema', 'ANDON SYSTEM')} - Vista de Proyección")
        
        # Variables
        self.proj_counter = None
        self.hora_actual = None
        self.fecha_actual = None
        self.frame_tabla = None
        self.timer_actualizacion = None
        
        self._configurar_ventana()
        self._setup_ui()
        self._iniciar_actualizaciones()
        
    def _configurar_ventana(self):
        """Configura la ventana según la configuración guardada"""
        fondo_color = self.config.get("color_fondo", "black")
        self.ventana.configure(bg=fondo_color)
        
        monitor_idx = self.config.get("monitor", 0)
        
        if self.config.get("pantalla_completa", False):
            self.ventana.attributes('-fullscreen', True)
            self.ventana.bind('<Escape>', lambda e: self._salir_pantalla_completa())
        else:
            ancho = self.config.get("ancho", 800)
            alto = self.config.get("alto", 600)
            x = self.config.get("x", 100)
            y = self.config.get("y", 100)
            self.ventana.geometry(f"{ancho}x{alto}+{x}+{y}")
            self.ventana.resizable(True, True)
            self._crear_controles()
        
        self.ventana.protocol("WM_DELETE_WINDOW", self._cerrar)
        
    def _crear_controles(self):
        """Crea controles para ventana no maximizada"""
        controles = tk.Frame(self.ventana, bg="#333333")
        controles.pack(fill="x", pady=(0, 5))
        
        tk.Button(controles,
                 text="✕ Cerrar",
                 bg="#ff5252",
                 fg="white",
                 font=("Segoe UI", 9),
                 relief="flat",
                 padx=10,
                 pady=3,
                 cursor="hand2",
                 command=self._cerrar).pack(side="right", padx=5, pady=3)
        
        tk.Button(controles,
                 text="💾 Guardar Posición",
                 bg="#4CAF50",
                 fg="white",
                 font=("Segoe UI", 9),
                 relief="flat",
                 padx=10,
                 pady=3,
                 cursor="hand2",
                 command=self._guardar_posicion).pack(side="right", padx=5, pady=3)
        
        tk.Label(controles,
                text="Arrastra para mover, borde para redimensionar",
                bg="#333333",
                fg="#AAAAAA",
                font=("Segoe UI", 8)).pack(side="left", padx=10, pady=3)
        
    def _setup_ui(self):
        """Configura la interfaz de usuario"""
        fondo = self.config.get("color_fondo", "black")
        texto = self.config.get("color_texto", "white")
        acento = self.config.get("color_acento", "#e94560")
        exito = self.config.get("color_exito", "#4CAF50")
        
        # Header
        header = tk.Frame(self.ventana, bg=fondo)
        header.pack(fill="x", pady=10)
        
        tk.Label(header,
                text=f"📺 {self.theme.colores.get('nombre_sistema', 'ANDON SYSTEM')} - PROYECCIÓN",
                bg=fondo,
                fg=texto,
                font=("Segoe UI", 20, "bold")).pack()
        
        tk.Label(header,
                text="Fallas Activas en Tiempo Real",
                bg=fondo,
                fg=texto,
                font=("Segoe UI", 14)).pack(pady=5)
        
        # Contador de fallas
        if self.config.get("mostrar_contador", True):
            counter_frame = tk.Frame(header, bg=fondo)
            counter_frame.pack(pady=10)
            
            self.proj_counter = tk.Label(counter_frame,
                                        text=str(len(self.falla_controller.fallas_activas)),
                                        bg=fondo,
                                        fg=texto,
                                        font=("Segoe UI", 36, "bold"))
            self.proj_counter.pack(side="left")
            
            tk.Label(counter_frame,
                    text="fallas activas",
                    bg=fondo,
                    fg=texto,
                    font=("Segoe UI", 12)).pack(side="left", padx=5)
        
        # Hora y fecha
        time_frame = tk.Frame(header, bg=fondo)
        time_frame.pack(pady=5)
        
        self.hora_actual = tk.Label(time_frame,
                                   text=datetime.now().strftime("%H:%M:%S"),
                                   bg=fondo,
                                   fg=exito,
                                   font=("Segoe UI", 30, "bold"))
        self.hora_actual.pack(side="left", padx=5)
        
        tk.Label(time_frame,
                text="|",
                bg=fondo,
                fg=texto,
                font=("Segoe UI", 12)).pack(side="left", padx=5)
        
        self.fecha_actual = tk.Label(time_frame,
                                    text=datetime.now().strftime("%d/%m/%Y"),
                                    bg=fondo,
                                    fg=texto,
                                    font=("Segoe UI", 30))
        self.fecha_actual.pack(side="left", padx=5)
        
        # Tabla de fallas
        self.frame_tabla = tk.Frame(self.ventana, bg=fondo)
        self.frame_tabla.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self._actualizar_tabla()
        
    def _actualizar_tabla(self):
        """Actualiza la tabla de fallas"""
        if not self.frame_tabla or not self.frame_tabla.winfo_exists():
            return
            
        # Limpiar tabla anterior
        for widget in self.frame_tabla.winfo_children():
            widget.destroy()
        
        fondo = self.config.get("color_fondo", "black")
        texto = self.config.get("color_texto", "white")
        acento = self.config.get("color_acento", "#e94560")
        
        # Filtrar fallas según configuración
        fallas_a_mostrar = self.falla_controller.fallas_activas
        if not self.config.get("mostrar_pendientes", True):
            fallas_a_mostrar = [a for a in fallas_a_mostrar if a.get("estado") != "pendiente"]
        
        # Actualizar contador
        if self.proj_counter and self.proj_counter.winfo_exists():
            self.proj_counter.config(text=str(len(fallas_a_mostrar)))
        
        if not fallas_a_mostrar:
            mensaje = "✅ No hay fallas activas"
            if not self.config.get("mostrar_pendientes", True) and any(a.get("estado") == "pendiente" for a in self.falla_controller.fallas_activas):
                mensaje = "👁️ Mostrando solo fallas activas (pendientes ocultas)"
            
            label = tk.Label(self.frame_tabla,
                           text=mensaje,
                           bg=fondo,
                           fg=self.config.get("color_exito", "#4CAF50"),
                           font=("Segoe UI", 24, "bold"))
            label.pack(expand=True)
            return
        
        # Determinar tamaño de fuente según ancho de ventana
        try:
            ancho = self.ventana.winfo_width()
            if ancho < 1000:
                tamaño_fuente = 14
                altura_fila = 40
            elif ancho < 1400:
                tamaño_fuente = 18
                altura_fila = 50
            else:
                tamaño_fuente = 22
                altura_fila = 60
        except:
            tamaño_fuente = 16
            altura_fila = 45
        
        # Crear tabla
        columnas = ("#", "Máquina", "Tipo", "Inicio", "Proceso", "Fin", "Estado")
        
        tree = ttk.Treeview(self.frame_tabla, columns=columnas, show="headings")
        
        # Configurar estilo
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Proyeccion.Treeview",
                       background=fondo,
                       foreground=texto,
                       rowheight=altura_fila,
                       fieldbackground=fondo,
                       borderwidth=0,
                       font=("Segoe UI", tamaño_fuente))
        style.configure("Proyeccion.Treeview.Heading",
                       background=acento,
                       foreground=texto,
                       relief="flat",
                       borderwidth=0,
                       font=("Segoe UI", tamaño_fuente + 2, "bold"))
        style.map('Proyeccion.Treeview',
                 background=[('selected', acento)],
                 foreground=[('selected', texto)])
        
        tree.configure(style="Proyeccion.Treeview")
        
        # Configurar columnas
        try:
            ancho_col = int(self.frame_tabla.winfo_width() / 7)
        except:
            ancho_col = 100
        
        for col in columnas:
            tree.heading(col, text=col)
            tree.column(col, width=ancho_col, anchor="center")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.frame_tabla, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Configurar colores por tipo
        tipos_unicos = set([a["tipo"] for a in fallas_a_mostrar])
        for tipo in tipos_unicos:
            color = self.theme.get_color_para_tipo(tipo)
            text_color = "#000000" if is_light_color(color) else "#FFFFFF"
            tree.tag_configure(tipo,
                              background=color,
                              foreground=text_color,
                              font=("Segoe UI", tamaño_fuente, "bold"))
        
        tree.tag_configure("pendiente", 
                          background=self.theme.colores.get("pendiente", "#FFA500"))
        
        # Insertar datos
        for alerta in fallas_a_mostrar:
            numero = alerta.get("numero_falla", "?")
            
            estado = alerta.get("estado", "activa")
            if estado == "pendiente":
                estado_text = "🟠 Pendiente"
                tags = (alerta["tipo"], "pendiente")
            elif estado == "en_proceso":
                estado_text = "🟡 En Proceso"
                tags = (alerta["tipo"],)
            elif estado == "resuelta":
                estado_text = "✅ Resuelta"
                tags = (alerta["tipo"],)
            else:
                estado_text = "🔴 Activa"
                tags = (alerta["tipo"],)
            
            valores = (
                f"#{numero}",
                alerta["maquina"],
                alerta["tipo"],
                solo_hora(alerta.get("inicio", "")),
                solo_hora(alerta.get("proceso", "")),
                solo_hora(alerta.get("fin", "")),
                estado_text
            )
            tree.insert("", "end", values=valores, tags=tags)
            
    def _iniciar_actualizaciones(self):
        """Inicia las actualizaciones periódicas"""
        self._actualizar_hora()
        self._programar_actualizacion_tabla()
        
    def _actualizar_hora(self):
        """Actualiza la hora en la pantalla"""
        if self.ventana and self.ventana.winfo_exists():
            ahora = datetime.now()
            if self.hora_actual and self.hora_actual.winfo_exists():
                self.hora_actual.config(text=ahora.strftime("%H:%M:%S"))
            if self.fecha_actual and self.fecha_actual.winfo_exists():
                self.fecha_actual.config(text=ahora.strftime("%d/%m/%Y"))
            self.ventana.after(1000, self._actualizar_hora)
            
    def _programar_actualizacion_tabla(self):
        """Programa la actualización periódica de la tabla"""
        if self.ventana and self.ventana.winfo_exists():
            self._actualizar_tabla()
            self.timer_actualizacion = self.ventana.after(2000, self._programar_actualizacion_tabla)
            
    def _guardar_posicion(self):
        """Guarda la posición actual de la ventana"""
        if self.ventana and not self.config.get("pantalla_completa", False):
            try:
                geometry = self.ventana.geometry()
                partes = geometry.split('+')
                tamaño = partes[0].split('x')
                self.config["ancho"] = int(tamaño[0])
                self.config["alto"] = int(tamaño[1])
                self.config["x"] = int(partes[1])
                self.config["y"] = int(partes[2])
                
                # Guardar en BD
                self.controller.config_model.guardar_config_proyeccion(self.config)
                
                # Mostrar mensaje temporal
                msg = tk.Label(self.ventana,
                              text="✓ Posición guardada",
                              bg="#4CAF50",
                              fg="white",
                              font=("Segoe UI", 10))
                msg.place(relx=0.5, rely=0.1, anchor="center")
                self.ventana.after(2000, msg.destroy)
                
            except Exception as e:
                logger.error(f"Error guardando posición: {e}")
                
    def _salir_pantalla_completa(self):
        """Sale del modo pantalla completa"""
        if self.ventana and self.ventana.attributes('-fullscreen'):
            self.ventana.attributes('-fullscreen', False)
            self._crear_controles()
            # Restaurar tamaño guardado
            ancho = self.config.get("ancho", 800)
            alto = self.config.get("alto", 600)
            x = self.config.get("x", 100)
            y = self.config.get("y", 100)
            self.ventana.geometry(f"{ancho}x{alto}+{x}+{y}")
            
    def _cerrar(self):
        """Cierra la ventana de proyección"""
        if self.timer_actualizacion:
            try:
                self.ventana.after_cancel(self.timer_actualizacion)
            except:
                pass
        
        if not self.config.get("pantalla_completa", False):
            self._guardar_posicion()
        
        try:
            self.ventana.destroy()
        except:
            pass