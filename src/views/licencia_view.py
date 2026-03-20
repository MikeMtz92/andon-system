# src/views/licencia_view.py

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from src.utils.widgets import ModernButton, ModernEntry
import logging

logger = logging.getLogger(__name__)

class LicenciaView:
    """Ventana de gestión de licencia"""
    
    def __init__(self, parent, controller, theme_service):
        self.parent = parent
        self.controller = controller
        self.theme = theme_service
        
        self.ventana = tk.Toplevel(parent)
        self.ventana.title("Gestión de Licencia")
        self.ventana.geometry("550x700")
        self.ventana.configure(bg=self.theme.colores["fondo"])
        self.ventana.resizable(False, False)
        self.ventana.transient(parent)
        self.ventana.grab_set()
        
        # Centrar ventana
        self.ventana.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (550 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (700 // 2)
        self.ventana.geometry(f"+{x}+{y}")
        
        self.config = controller.licencia_controller.config.copy()
        self._setup_ui()
        
    def _setup_ui(self):
        """Configura la interfaz de usuario"""
        # Título
        tk.Label(self.ventana,
                text="🔐 Gestión de Licencia Andon",
                bg=self.theme.colores["fondo"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 18, "bold")).pack(pady=20)
        
        # Frame principal con scroll
        container = tk.Frame(self.ventana, bg=self.theme.colores["fondo"])
        container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        canvas = tk.Canvas(container, bg=self.theme.colores["fondo"], highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.theme.colores["fondo"])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=canvas.winfo_width())
        canvas.configure(yscrollcommand=scrollbar.set)
        
        def configure_width(event):
            canvas.itemconfig(1, width=event.width)
        
        canvas.bind('<Configure>', configure_width)
        
        # ===== ID DE INSTALACIÓN =====
        self._crear_seccion_id(scrollable_frame)
        
        # ===== ESTADO ACTUAL =====
        self._crear_seccion_estado(scrollable_frame)
        
        # ===== FECHAS IMPORTANTES =====
        self._crear_seccion_fechas(scrollable_frame)
        
        # ===== CAMBIAR LICENCIA =====
        self._crear_seccion_cambiar(scrollable_frame)
        
        # ===== INFORMACIÓN DE LICENCIAS =====
        self._crear_seccion_info(scrollable_frame)
        
        # ===== BOTONES DE ACCIÓN =====
        self._crear_botones_accion(scrollable_frame)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.ventana.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        
    def _crear_seccion_id(self, parent):
        """Crea la sección de ID de instalación"""
        card = tk.Frame(parent, bg=self.theme.colores["card"], relief="flat", bd=1)
        card.pack(fill="x", pady=(0, 15))
        
        tk.Label(card,
                text="🆔 ID de Instalación",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15, pady=(15, 5))
        
        id_frame = tk.Frame(card, bg=self.theme.colores["card"])
        id_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        id_label = tk.Label(id_frame,
                           text=self.config['installation_id'],
                           bg=self.theme.colores["fondo"],
                           fg=self.theme.colores["accento"],
                           font=("Consolas", 12, "bold"),
                           padx=10,
                           pady=5)
        id_label.pack(side="left")
        
        tk.Button(id_frame,
                 text="📋 Copiar",
                 bg=self.theme.colores["card"],
                 fg=self.theme.colores["texto"],
                 font=("Segoe UI", 8),
                 relief="flat",
                 padx=8,
                 pady=2,
                 cursor="hand2",
                 command=lambda: self._copiar_id()).pack(side="left", padx=5)
        
    def _crear_seccion_estado(self, parent):
        """Crea la sección de estado actual"""
        card = tk.Frame(parent, bg=self.theme.colores["card"], relief="flat", bd=1)
        card.pack(fill="x", pady=(0, 15))
        
        tk.Label(card,
                text="📊 Estado Actual",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15, pady=(15, 10))
        
        # Tipo de licencia
        tipo_frame = tk.Frame(card, bg=self.theme.colores["card"])
        tipo_frame.pack(fill="x", padx=15, pady=5)
        
        tk.Label(tipo_frame,
                text="Tipo:",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto_secundario"],
                width=15,
                anchor="w").pack(side="left")
        
        tipo_text = self.config.get('license_type', 'basic').upper()
        if tipo_text == 'PRO':
            color_tipo = "#4CAF50"
            descripcion = "✓ Todas las funciones"
        elif tipo_text == 'MID':
            color_tipo = "#FFC107"
            descripcion = "✓ Funciones intermedias"
        elif tipo_text == 'DEMO':
            color_tipo = "#9C27B0"
            descripcion = "✓ Versión de prueba (PRO)"
            tipo_text = "DEMO (PRO)"
        else:
            color_tipo = "#FF5252"
            descripcion = "✗ Funciones básicas"
        
        tk.Label(tipo_frame,
                text=tipo_text,
                bg=color_tipo,
                fg="white" if tipo_text not in ['MID', 'DEMO (PRO)'] else "black",
                font=("Segoe UI", 10, "bold"),
                padx=10,
                pady=2).pack(side="left", padx=(0, 10))
        
        tk.Label(tipo_frame,
                text=descripcion,
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto_secundario"],
                font=("Segoe UI", 9, "italic")).pack(side="left")
        
        # Límites
        limites_frame = tk.Frame(card, bg=self.theme.colores["card"])
        limites_frame.pack(fill="x", padx=15, pady=5)
        
        tk.Label(limites_frame,
                text="Tipos de falla:",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto_secundario"],
                width=20,
                anchor="w").pack(side="left")
        
        tk.Label(limites_frame,
                text=str(self.config.get('max_fallas', 3)),
                bg=self.theme.colores["card"],
                fg=self.theme.colores["success"],
                font=("Segoe UI", 11, "bold")).pack(side="left")
        
        limites2_frame = tk.Frame(card, bg=self.theme.colores["card"])
        limites2_frame.pack(fill="x", padx=15, pady=5)
        
        tk.Label(limites2_frame,
                text="Límite máquinas:",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto_secundario"],
                width=20,
                anchor="w").pack(side="left")
        
        tk.Label(limites2_frame,
                text=str(self.config.get('max_maquinas', 5)),
                bg=self.theme.colores["card"],
                fg=self.theme.colores["success"],
                font=("Segoe UI", 11, "bold")).pack(side="left")
        
    def _crear_seccion_fechas(self, parent):
        """Crea la sección de fechas importantes"""
        card = tk.Frame(parent, bg=self.theme.colores["card"], relief="flat", bd=1)
        card.pack(fill="x", pady=(0, 15))
        
        tk.Label(card,
                text="📅 Fechas Importantes",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15, pady=(15, 10))
        
        # Demo
        demo_frame = tk.Frame(card, bg=self.theme.colores["card"])
        demo_frame.pack(fill="x", padx=15, pady=5)
        
        tk.Label(demo_frame,
                text="Demo:",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto_secundario"],
                width=15,
                anchor="w").pack(side="left")
        
        if self.config.get('demo_expires'):
            try:
                fecha_demo = datetime.strptime(self.config['demo_expires'], "%Y-%m-%d")
                dias_restantes = (fecha_demo - datetime.now().date()).days
                color_dias = "#4CAF50" if dias_restantes > 7 else "#FFC107" if dias_restantes > 0 else "#FF5252"
                
                tk.Label(demo_frame,
                        text=f"{self.config['demo_expires']} ({dias_restantes} días)",
                        bg=self.theme.colores["card"],
                        fg=color_dias,
                        font=("Segoe UI", 10, "bold")).pack(side="left")
            except:
                tk.Label(demo_frame,
                        text=self.config['demo_expires'],
                        bg=self.theme.colores["card"],
                        fg=self.theme.colores["texto"],
                        font=("Segoe UI", 10)).pack(side="left")
        else:
            tk.Label(demo_frame,
                    text="No activada",
                    bg=self.theme.colores["card"],
                    fg=self.theme.colores["texto_secundario"],
                    font=("Segoe UI", 10, "italic")).pack(side="left")
        
        # Licencia de pago
        if self.config.get('license_key') and self.config.get('license_type') != 'demo':
            lic_frame = tk.Frame(card, bg=self.theme.colores["card"])
            lic_frame.pack(fill="x", padx=15, pady=5)
            
            tk.Label(lic_frame,
                    text="Licencia:",
                    bg=self.theme.colores["card"],
                    fg=self.theme.colores["texto_secundario"],
                    width=15,
                    anchor="w").pack(side="left")
            
            tk.Label(lic_frame,
                    text="✓ Activa",
                    bg=self.theme.colores["card"],
                    fg=self.theme.colores["success"],
                    font=("Segoe UI", 10, "bold")).pack(side="left")
        
        # Última validación
        if self.config.get('last_validation'):
            valid_frame = tk.Frame(card, bg=self.theme.colores["card"])
            valid_frame.pack(fill="x", padx=15, pady=5)
            
            tk.Label(valid_frame,
                    text="Última validación:",
                    bg=self.theme.colores["card"],
                    fg=self.theme.colores["texto_secundario"],
                    width=15,
                    anchor="w").pack(side="left")
            
            try:
                fecha_valid = datetime.strptime(self.config['last_validation'], "%Y-%m-%d %H:%M:%S")
                tk.Label(valid_frame,
                        text=fecha_valid.strftime("%d/%m/%Y %H:%M"),
                        bg=self.theme.colores["card"],
                        fg=self.theme.colores["texto"],
                        font=("Segoe UI", 10)).pack(side="left")
            except:
                tk.Label(valid_frame,
                        text=self.config['last_validation'],
                        bg=self.theme.colores["card"],
                        fg=self.theme.colores["texto"],
                        font=("Segoe UI", 10)).pack(side="left")
        
    def _crear_seccion_cambiar(self, parent):
        """Crea la sección para cambiar licencia"""
        card = tk.Frame(parent, bg=self.theme.colores["card"], relief="flat", bd=1)
        card.pack(fill="x", pady=(0, 15))
        
        tk.Label(card,
                text="🔄 Cambiar Licencia",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15, pady=(15, 10))
        
        btn_frame = tk.Frame(card, bg=self.theme.colores["card"])
        btn_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        tk.Button(btn_frame,
                 text="🔑 Activar Nueva Licencia",
                 bg=self.theme.colores["success"],
                 fg=self.theme.colores["texto"],
                 font=("Segoe UI", 11, "bold"),
                 relief="flat",
                 padx=20,
                 pady=8,
                 cursor="hand2",
                 command=self._mostrar_activacion).pack(fill="x", pady=5)
        
        tk.Button(btn_frame,
                 text="🎁 Iniciar Demo (15 días)",
                 bg=self.theme.colores["warning"],
                 fg=self.theme.colores["negro"],
                 font=("Segoe UI", 11),
                 relief="flat",
                 padx=20,
                 pady=8,
                 cursor="hand2",
                 command=self._iniciar_demo).pack(fill="x", pady=5)
        
        tk.Button(btn_frame,
                 text="🔄 Desactivar Licencia Actual",
                 bg=self.theme.colores["danger"],
                 fg=self.theme.colores["texto"],
                 font=("Segoe UI", 11),
                 relief="flat",
                 padx=20,
                 pady=8,
                 cursor="hand2",
                 command=self._desactivar_licencia).pack(fill="x", pady=5)
        
    def _crear_seccion_info(self, parent):
        """Crea la sección de información de licencias"""
        card = tk.Frame(parent, bg=self.theme.colores["card"], relief="flat", bd=1)
        card.pack(fill="x", pady=(0, 15))
        
        tk.Label(card,
                text="ℹ️ Información de Licencias",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15, pady=(15, 10))
        
        info_text = tk.Text(card,
                          height=8,
                          width=50,
                          bg=self.theme.colores.get("superficie3", "#2d3047"),
                          fg=self.theme.colores["texto"],
                          font=("Segoe UI", 9),
                          relief="flat",
                          wrap="word")
        info_text.pack(fill="x", padx=15, pady=(0, 15))
        info_text.insert("1.0", self._obtener_info_licencias())
        info_text.config(state="disabled")
        
    def _crear_botones_accion(self, parent):
        """Crea los botones de acción"""
        btn_frame = tk.Frame(parent, bg=self.theme.colores["fondo"])
        btn_frame.pack(fill="x", pady=10)
        
        tk.Button(btn_frame,
                 text="🔄 Validar Ahora",
                 bg=self.theme.colores["warning"],
                 fg=self.theme.colores["negro"],
                 font=("Segoe UI", 11),
                 relief="flat",
                 padx=20,
                 pady=10,
                 cursor="hand2",
                 command=self._validar_ahora).pack(side="left", padx=5)
        
        tk.Button(btn_frame,
                 text="❌ Cerrar",
                 bg=self.theme.colores["danger"],
                 fg=self.theme.colores["texto"],
                 font=("Segoe UI", 11),
                 relief="flat",
                 padx=20,
                 pady=10,
                 cursor="hand2",
                 command=self.ventana.destroy).pack(side="right", padx=5)
        
    def _obtener_info_licencias(self):
        """Retorna texto informativo sobre tipos de licencia"""
        return """📋 TIPOS DE LICENCIA:

🔴 BASIC (Gratuita):
  • 3 TIPOS de falla máximo
  • 5 máquinas máximo
  • MySQL
  • Sin gráficas en Excel

🟡 MID ($):
  • 4 TIPOS de falla máximo
  • 15 máquinas máximo
  • 1 exportación Excel/día con gráficas
  • Configuración avanzada

🟢 PRO ($$):
  • 5+ TIPOS de falla
  • 200+ máquinas
  • MySQL 
  • Exportación ilimitada
  • Código ESP32
  • Todas las funciones

🎁 DEMO (15 días):
  • Acceso completo PRO
  • 15 días de prueba"""
        
    def _copiar_id(self):
        """Copia el ID de instalación al portapapeles"""
        self.ventana.clipboard_clear()
        self.ventana.clipboard_append(self.config['installation_id'])
        messagebox.showinfo("Copiado", "ID de instalación copiado al portapapeles")
        
    def _mostrar_activacion(self):
        """Muestra el diálogo de activación de licencia"""
        try:
            ventana = VentanaActivacion(self.ventana, self.controller, self.config)
            self.ventana.wait_window(ventana.ventana)
            
            if ventana.resultado:
                self.config = ventana.resultado
                self.controller.licencia_controller.config = ventana.resultado
                self.controller.licencia_controller._verificar_y_aplicar()
                
                # Cerrar la ventana de licencia primero
                self.ventana.destroy()
                
                # Mostrar mensaje de éxito
                import tkinter.messagebox as msgbox
                msgbox.showinfo("Licencia Actualizada",
                            "La licencia ha sido actualizada correctamente.\n\n"
                            "La aplicación se reiniciará para aplicar los cambios.")
                
                # Reiniciar
                self._reiniciar_aplicacion()
        except Exception as e:
            print(f"Error en activación: {e}")

    def _reiniciar_aplicacion(self):
        """Reinicia la aplicación para aplicar los cambios de licencia"""
        import sys
        import subprocess
        import os
        import time
        
        # Obtener el PID del proceso actual
        current_pid = os.getpid()
        
        # Cerrar la ventana principal
        try:
            self.parent.destroy()
        except:
            pass
        
        # Cerrar la ventana de licencia si existe
        try:
            self.ventana.destroy()
        except:
            pass
        
        # Forzar salida del hilo principal de Tkinter
        try:
            self.parent.quit()
        except:
            pass
        
        # Esperar un momento para que la ventana se cierre
        time.sleep(0.5)
        
        # Ejecutar nueva instancia
        subprocess.Popen([sys.executable, sys.argv[0]])
        
        # Forzar salida del proceso actual
        os._exit(0)
        
    def _iniciar_demo(self):
        """Inicia periodo de demo"""
        if self.config.get('demo_used'):
            messagebox.showerror("Error", "Ya has utilizado el periodo de demo")
            return
        
        respuesta = messagebox.askyesno(
            "Confirmar Demo",
            "¿Estás seguro de iniciar el periodo de demo de 15 días?\n\n"
            "Esta acción no se puede deshacer."
        )
        
        if not respuesta:
            return
        
        exito, info = self.controller.licencia_controller.iniciar_demo(
            self.config['installation_id']
        )
        
        if exito:
            self.config.update({
                'demo_used': True,
                'demo_start': datetime.now().strftime("%Y-%m-%d"),
                'demo_expires': info,
                'license_type': 'demo'
            })
            messagebox.showinfo("🎁 Demo Activado",
                              f"Periodo de demo activado hasta: {info}")
            self.ventana.destroy()
        else:
            messagebox.showerror("Error", f"No se pudo iniciar demo:\n{info}")
            
    def _desactivar_licencia(self):
        """Desactiva la licencia actual y vuelve a básico"""
        if not self.config.get('license_key') and not self.config.get('demo_used'):
            messagebox.showinfo("Información", "No hay una licencia activa para desactivar")
            return
        
        respuesta = messagebox.askyesno(
            "⚠️ Confirmar Desactivación",
            "¿Estás seguro de desactivar la licencia actual?\n\n"
            "Volverás al modo básico."
        )
        
        if respuesta:
            self.controller.licencia_controller.desactivar_licencia()
            self.config = self.controller.licencia_controller.config
            messagebox.showinfo("✅ Licencia Desactivada",
                              "Ahora estás usando el modo básico")
            self.ventana.destroy()
            
    def _validar_ahora(self):
        """Valida el estado actual de la licencia"""
        valida, info = self.controller.licencia_controller.licencia_model.verificar_estado_licencia(
            self.config
        )
        
        if valida:
            self.config = self.controller.licencia_controller.cargar_licencia()
            messagebox.showinfo("✅ Licencia Válida",
                              f"Tipo: {self.config.get('license_type', 'desconocido').upper()}")
            self.ventana.destroy()
        else:
            messagebox.showwarning("⚠️ Atención",
                                 info if isinstance(info, str) else "Licencia no válida")

class VentanaActivacion:
    """Diálogo para activación de licencia"""
    
    def __init__(self, parent, controller, config):
        self.parent = parent
        self.controller = controller
        self.config = config
        self.resultado = None
        
        self.ventana = tk.Toplevel(parent)
        self.ventana.title("Activación de Licencia")
        self.ventana.geometry("500x400")
        # CORREGIDO: usar theme_service en lugar de theme
        self.ventana.configure(bg=self.controller.theme_service.colores["fondo"])
        self.ventana.resizable(False, False)
        self.ventana.transient(parent)
        self.ventana.grab_set()
        
        # Centrar
        self.ventana.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (500 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (400 // 2)
        self.ventana.geometry(f"+{x}+{y}")
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Configura la interfaz de usuario"""
        # CORREGIDO: usar theme_service en lugar de theme
        theme = self.controller.theme_service
        
        tk.Label(self.ventana,
                text="🔐 Activación de Licencia Andon",
                bg=theme.colores["fondo"],
                fg=theme.colores["texto"],
                font=("Segoe UI", 16, "bold")).pack(pady=20)
        
        tk.Label(self.ventana,
                text=f"ID de Instalación:",
                bg=theme.colores["fondo"],
                fg=theme.colores["texto_secundario"],
                font=("Segoe UI", 10)).pack(pady=(10, 0))
        
        tk.Label(self.ventana,
                text=self.config['installation_id'],
                bg=theme.colores["card"],
                fg=theme.colores["accento"],
                font=("Segoe UI", 10, "bold"),
                padx=20,
                pady=10).pack()
        
        tk.Label(self.ventana,
                text="Ingresa tu clave de licencia:",
                bg=theme.colores["fondo"],
                fg=theme.colores["texto"],
                font=("Segoe UI", 11)).pack(pady=(10, 5))
        
        self.entry_licencia = tk.Entry(self.ventana,
                                      width=30,
                                      bg=theme.colores.get("superficie3", "#2d3047"),
                                      fg=theme.colores["texto"],
                                      font=("Segoe UI", 11),
                                      relief="flat")
        self.entry_licencia.pack(pady=10)
        
        btn_frame = tk.Frame(self.ventana, bg=theme.colores["fondo"])
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame,
                 text="✅ Activar Licencia",
                 bg=theme.colores["success"],
                 fg=theme.colores["texto"],
                 font=("Segoe UI", 11, "bold"),
                 relief="flat",
                 padx=20,
                 pady=10,
                 cursor="hand2",
                 command=self._activar).pack(side="left", padx=5)
        
        tk.Button(btn_frame,
                 text="❌ Cancelar",
                 bg=theme.colores["danger"],
                 fg=theme.colores["texto"],
                 font=("Segoe UI", 11),
                 relief="flat",
                 padx=20,
                 pady=10,
                 cursor="hand2",
                 command=self.ventana.destroy).pack(side="left", padx=5)
        
    def _activar(self):
        """Activa la licencia ingresada"""
        license_key = self.entry_licencia.get().strip()
        if not license_key:
            messagebox.showerror("Error", "Ingresa una clave de licencia", parent=self.ventana)
            return
        
        print(f"🔍 Validando licencia: {license_key}")
        
        exito, info = self.controller.licencia_controller.activar_licencia(
            license_key, self.config['installation_id']
        )
        
        if exito:
            # Cerrar la ventana de activación
            self.ventana.destroy()
            # Mostrar mensaje de éxito
            messagebox.showinfo("✅ Éxito",
                            f"Licencia {info} activada correctamente.\n\n"
                            "La aplicación se reiniciará para aplicar los cambios.")
            # Llamar al reinicio
            self._reiniciar_aplicacion()
        else:
            messagebox.showerror("❌ Error", f"Licencia no válida:\n{info}", parent=self.ventana)

    # src/views/licencia_view.py

    def _reiniciar_aplicacion(self):
        """Reinicia la aplicación para aplicar los cambios de licencia"""
        import sys
        import subprocess
        import os
        import time
        
        # Obtener el PID del proceso actual
        current_pid = os.getpid()
        
        # Cerrar la ventana principal
        try:
            self.parent.destroy()
        except:
            pass
        
        # Cerrar la ventana de licencia si existe
        try:
            self.ventana.destroy()
        except:
            pass
        
        # Forzar salida del hilo principal de Tkinter
        try:
            self.parent.quit()
        except:
            pass
        
        # Esperar un momento para que la ventana se cierre
        time.sleep(0.5)
        
        # Ejecutar nueva instancia
        subprocess.Popen([sys.executable, sys.argv[0]])
        
        # Forzar salida del proceso actual
        os._exit(0)