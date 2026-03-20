# src/views/main_view.py

import tkinter as tk
from tkinter import ttk
import logging
from src.utils.widgets import ModernButton, ModernEntry, ModernCombobox

logger = logging.getLogger(__name__)

class MainView:
    """Ventana principal con menú lateral y área de contenido"""
    
    def __init__(self, root, controller, theme_service, falla_controller):
        self.root = root
        self.controller = controller
        self.theme = theme_service
        self.falla_controller = falla_controller
        
        self.root.title("ReAction - Panel de Control")
        self.root.geometry("1400x800")
        self.root.configure(bg=self.theme.colores["fondo"])
        
        # Vistas - las crearemos bajo demanda
        self.current_view = None
        self.andon_view = None
        self.historial_view = None
        
        self._setup_ui()
        self._setup_styles()
        
        # Mostrar vista principal por defecto
        self.show_andon_view()

    def _setup_styles(self):
        """Configura los estilos de ttk"""
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview",
                        background=self.theme.colores["card"],
                        foreground=self.theme.colores["texto"],
                        rowheight=35,
                        fieldbackground=self.theme.colores["card"],
                        borderwidth=0,
                        font=("Segoe UI", 10))
        style.configure("Treeview.Heading",
                        background=self.theme.colores["sidebar"],
                        foreground=self.theme.colores["texto"],
                        relief="flat",
                        borderwidth=0,
                        font=("Segoe UI", 11, "bold"))
        style.map('Treeview',
                  background=[('selected', self.theme.colores["accento"])],
                  foreground=[('selected', self.theme.colores["texto"])])

    def _setup_ui(self):
        """Crea la interfaz de usuario principal"""
        # Sidebar
        self.sidebar = tk.Frame(self.root, bg=self.theme.colores["sidebar"], width=250)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Header del sidebar
        header = tk.Frame(self.sidebar, bg=self.theme.colores["sidebar"], height=80)
        header.pack(fill="x", pady=(0, 20))
        header.pack_propagate(False)

        self.logo_label = tk.Label(header,
                                  text=f"⚙️ {self.theme.colores.get('nombre_sistema', 'ANDON SYSTEM')}",
                                  bg=self.theme.colores["sidebar"],
                                  fg=self.theme.colores["texto"],
                                  font=("Segoe UI", 16, "bold"))
        self.logo_label.pack(pady=25)

        # Botones de navegación
        nav_buttons = [
            ("📊 Andon en Vivo", self.show_andon_view),
            ("📋 Historial", self.show_historial_view),
            ("📺 Proyección", self._on_proyeccion_click),
            ("⚙️ Configuración", self._on_configuracion_click),
            ("📈 Estadísticas", self._on_estadisticas_click),
            ("🤖 Generar Código ESP32", self._on_esp32_click),
            ("🔐 Licencia", self._on_licencia_click)
        ]

        for text, command in nav_buttons:
            btn = tk.Button(self.sidebar,
                          text=text,
                          command=command,
                          bg=self.theme.colores["sidebar"],
                          fg=self.theme.colores["texto_secundario"],
                          font=("Segoe UI", 11),
                          relief="flat",
                          anchor="w",
                          padx=20,
                          pady=15,
                          cursor="hand2")
            btn.pack(fill="x")
            btn.bind("<Enter>", lambda e, b=btn: b.config(
                bg=self.theme.colores["accento"], 
                fg=self.theme.colores["texto"]))
            btn.bind("<Leave>", lambda e, b=btn, t=text: b.config(
                bg=self.theme.colores["sidebar"], 
                fg=self.theme.colores["texto_secundario"]))

        # Área de contenido principal
        self.main_content = tk.Frame(self.root, bg=self.theme.colores["fondo"])
        self.main_content.pack(side="right", fill="both", expand=True)

        # Header del contenido
        self.header_frame = tk.Frame(self.main_content, bg=self.theme.colores["card"], height=70)
        self.header_frame.pack(fill="x", padx=20, pady=(20, 10))
        self.header_frame.pack_propagate(False)

        self.header_label = tk.Label(self.header_frame,
                                    text="Panel de Control Andon",
                                    bg=self.theme.colores["card"],
                                    fg=self.theme.colores["texto"],
                                    font=("Segoe UI", 18, "bold"))
        self.header_label.pack(side="left", padx=30)

        # Indicador de estado
        self.status_frame = tk.Frame(self.header_frame, bg=self.theme.colores["card"])
        self.status_frame.pack(side="right", padx=30)

        self.status_indicator = tk.Label(self.status_frame,
                                        text="●",
                                        bg="#4CAF50",
                                        fg="#4CAF50",
                                        font=("Arial", 14))
        self.status_indicator.pack(side="left")

        self.status_label = tk.Label(self.status_frame,
                                    text="Sistema Activo",
                                    bg=self.theme.colores["card"],
                                    fg=self.theme.colores["texto_secundario"],
                                    font=("Segoe UI", 10))
        self.status_label.pack(side="left", padx=5)

        # Área de contenido variable
        self.content_area = tk.Frame(self.main_content, bg=self.theme.colores["fondo"])
        self.content_area.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def show_andon_view(self):
        """Muestra la vista de Andon en Vivo"""
        from src.views.andon_view import AndonView
        
        self.header_label.config(text="Panel de Control Andon")
        
        # Ocultar vista actual si existe
        if self.current_view:
            self.current_view.pack_forget()
        
        # Crear vista si no existe
        if not self.andon_view or not self.andon_view.winfo_exists():
            self.andon_view = AndonView(self.content_area, self.controller, 
                                       self.theme, self.falla_controller)
        
        # Mostrar vista
        self.andon_view.pack(fill="both", expand=True)
        self.current_view = self.andon_view
        
        # Actualizar datos
        self.andon_view.actualizar_tabla()
        self.andon_view.update_stats()

    def show_historial_view(self):
        """Muestra la vista de Historial"""
        from src.views.historial_view import HistorialView
        
        self.header_label.config(text="Historial de Fallas")
        
        # Ocultar vista actual si existe
        if self.current_view:
            self.current_view.pack_forget()
        
        # Crear vista si no existe
        if not self.historial_view or not self.historial_view.winfo_exists():
            self.historial_view = HistorialView(self.content_area, self.controller,
                                              self.theme, self.falla_controller)
        
        # Mostrar vista
        self.historial_view.pack(fill="both", expand=True)
        self.current_view = self.historial_view

    def _on_proyeccion_click(self):
        """Maneja clic en botón Proyección"""
        if self.controller.licencia_controller.puede_configurar_proyeccion:
            from src.views.proyeccion_view import ProyeccionView
            ProyeccionView(self.root, self.controller, self.theme, self.falla_controller)
        else:
            self._mostrar_proyeccion_simple()

    def _mostrar_proyeccion_simple(self):
        """Muestra versión simple de proyección"""
        from src.views.proyeccion_view import ProyeccionView
        # Usar la misma vista pero con configuración por defecto
        ProyeccionView(self.root, self.controller, self.theme, self.falla_controller)

    def _on_configuracion_click(self):
        """Maneja clic en botón Configuración"""
        if not self.controller.licencia_controller.puede_configurar:
            from tkinter import messagebox
            messagebox.showinfo("Acceso Restringido",
                              "La configuración requiere licencia MID o PRO")
            return
        
        from src.views.config_view import ConfigView
        ConfigView(self.root, self.controller, self.theme, self.falla_controller)

    def _on_estadisticas_click(self):
        """Maneja clic en botón Estadísticas"""
        from src.views.estadisticas_view import EstadisticasView
        EstadisticasView(self.root, self.controller, self.theme, self.falla_controller)

    def _on_esp32_click(self):
        """Maneja clic en botón ESP32"""
        if not self.controller.licencia_controller.puede_generar_esp32:
            from tkinter import messagebox
            messagebox.showinfo("Acceso Restringido",
                              "Generar código ESP32 requiere licencia PRO")
            return
        
        from src.views.esp32_view import ESP32View
        ESP32View(self.root, self.controller, self.theme, self.falla_controller)

    def _on_licencia_click(self):
        """Maneja clic en botón Licencia"""
        from src.views.licencia_view import LicenciaView
        LicenciaView(self.root, self.controller, self.theme)

    def actualizar_fallas(self):
        """Actualiza todas las vistas cuando cambian las fallas"""
        try:
            if self.andon_view and self.andon_view.winfo_exists():
                self.andon_view.actualizar_tabla()
                self.andon_view.update_stats()
        except Exception as e:
            logger.error(f"Error actualizando AndonView: {e}")
        
        try:
            if self.historial_view and self.historial_view.winfo_exists():
                self.historial_view.actualizar()
        except Exception as e:
            logger.error(f"Error actualizando HistorialView: {e}")