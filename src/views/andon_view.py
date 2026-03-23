# src/views/andon_view.py

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import threading
import winsound
from src.utils.widgets import ModernButton, ModernEntry, ModernCombobox
from src.utils.helpers import solo_hora, lighten_color, is_light_color
import logging

logger = logging.getLogger(__name__)

class AndonView(tk.Frame):
    """Vista principal de Andon en Vivo"""
    
    def __init__(self, parent, controller, theme_service, falla_controller):
        super().__init__(parent, bg=theme_service.colores["fondo"])
        self.root = parent
        self.controller = controller
        self.theme = theme_service
        self.falla_controller = falla_controller
        self.stats_widgets = {}
        
        # Variables
        self.tipos_falla = []
        self.maquinas = self.controller.get_maquinas_permitidas()
        self.treeview_principal = None
        self.treeview_item_data = {}
        self.stats_container = None
        self.contador_fallas = None
        self.pendientes_btn_frame = None
        self.ocultar_pendientes_var = tk.BooleanVar(value=False)
        
        # Configurar callbacks
        self.falla_controller.on_fallas_actualizadas = self.actualizar_tabla
        
        self._setup_ui()
        self._cargar_tipos_falla()
        self._actualizar_botones_tipos()
        self.actualizar_tabla()
        self.update_stats()

    def _setup_ui(self):
        """Configura la interfaz de usuario"""
        # ===== REGISTRO RÁPIDO =====
        quick_frame = tk.Frame(self, bg=self.theme.colores["card"])
        quick_frame.pack(fill="x", padx=20, pady=20)

        tk.Label(quick_frame,
                text="Registro Rápido",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 15))

        input_row = tk.Frame(quick_frame, bg=self.theme.colores["card"])
        input_row.pack(fill="x")

        tk.Label(input_row,
                text="Máquina:",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto_secundario"],
                font=("Segoe UI", 10)).pack(side="left", padx=(0, 10))

        self.entrada_maquina = ModernCombobox(input_row, theme_service=self.theme,
                                            values=self.maquinas, width=15)
        self.entrada_maquina.pack(side="left", padx=(0, 30))

        self.tipos_frame = tk.Frame(input_row, bg=self.theme.colores["card"])
        self.tipos_frame.pack(side="left", padx=10)

        # ===== ESTADÍSTICAS =====
        stats_frame = tk.Frame(self, bg=self.theme.colores["card"])
        stats_frame.pack(fill="x", padx=20, pady=(0, 20))

        button_row = tk.Frame(stats_frame, bg=self.theme.colores["card"])
        button_row.pack(fill="x", padx=20, pady=(10, 5))

        tk.Label(button_row,
                text="Estadísticas en Tiempo Real",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 12, "bold")).pack(side="left")

        # Botones de acción (siempre visibles)
        tk.Button(button_row,
                text="🔴 CERRAR TODAS",
                bg=self.theme.colores["danger"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 9, "bold"),
                relief="flat",
                padx=8,
                pady=3,
                cursor="hand2",
                command=self._on_cerrar_todas).pack(side="right", padx=2)

        tk.Button(button_row,
                text="🔄 ACTUALIZAR BD",
                bg=self.theme.colores["success"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 9, "bold"),
                relief="flat",
                padx=8,
                pady=3,
                cursor="hand2",
                command=self._on_actualizar_manual).pack(side="right", padx=2)

        # Frame para botones de pendientes (se mostrará según licencia)
        self.pendientes_btn_frame = tk.Frame(button_row, bg=self.theme.colores["card"])
        self._actualizar_botones_pendientes()

        # Contenedor de estadísticas
        self.stats_container = tk.Frame(stats_frame, bg=self.theme.colores["card"])
        self.stats_container.pack(fill="x", padx=20, pady=(5, 15))
        
        # Crear widgets de estadísticas
        self._crear_widgets_estadisticas()

        # Contador de fallas
        counter_frame = tk.Frame(stats_frame, bg=self.theme.colores["card"])
        counter_frame.pack(fill="x", padx=20, pady=(0, 15))

        self.contador_fallas = tk.Label(counter_frame,
                                       text="0 activas",
                                       bg=self.theme.colores["accento"],
                                       fg=self.theme.colores["texto"],
                                       font=("Segoe UI", 10, "bold"),
                                       padx=15,
                                       pady=5)
        self.contador_fallas.pack(side="left")

        # ===== TABLA DE FALLAS ACTIVAS =====
        tabla_container = tk.Frame(self, bg=self.theme.colores["fondo"])
        tabla_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        tk.Label(tabla_container,
                text="Fallas Activas",
                bg=self.theme.colores["fondo"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 10))

        self.frame_tabla = tk.Frame(tabla_container, bg=self.theme.colores["fondo"])
        self.frame_tabla.pack(fill="both", expand=True)

        self._crear_tabla_principal()

    def _cargar_tipos_falla(self):
        """Carga los tipos de falla desde el controlador"""
        try:
            tipos_data = self.falla_controller.falla_model.cargar_tipos_falla()
            if tipos_data:
                self.tipos_falla = [t["nombre"] for t in tipos_data]
                print(f"Tipos cargados: {self.tipos_falla}")  # Debug
            else:
                print("No se encontraron tipos, usando valores por defecto")
                self.tipos_falla = ["Mantenimiento", "Producción", "Calidad"]
            
            # Limitar según licencia
            max_tipos = self.controller.licencia_controller.max_tipos_falla
            if len(self.tipos_falla) > max_tipos:
                self.tipos_falla = self.tipos_falla[:max_tipos]
                
        except Exception as e:
            print(f"Error cargando tipos: {e}")
            self.tipos_falla = ["Mantenimiento", "Producción", "Calidad"]

    def _actualizar_botones_tipos(self):
        """Actualiza los botones de tipos de falla en registro rápido"""
        for widget in self.tipos_frame.winfo_children():
            widget.destroy()

        for tipo in self.tipos_falla:
            color = self.theme.get_color_para_tipo(tipo)
            print(f"Botón {tipo} color: {color}")  # Debug
            
            # Determinar color del texto
            texto_color = "#000000" if self._is_light_color(color) else "#FFFFFF"
            
            btn = tk.Button(self.tipos_frame,
                        text=tipo,
                        command=lambda t=tipo: self._on_registro_manual(t),
                        bg=color,
                        fg=texto_color,
                        font=("Segoe UI", 9, "bold"),
                        relief="flat",
                        padx=15,
                        pady=8,
                        cursor="hand2")
            btn.pack(side="left", padx=5)
            btn.bind("<Enter>", lambda e, b=btn, c=color: 
                    b.config(bg=self._lighten_color(c, 0.1)))
            btn.bind("<Leave>", lambda e, b=btn, c=color: 
                    b.config(bg=c))
            
    def _is_light_color(self, color):
        """Determina si un color es claro"""
        if color.startswith('#'):
            color = color.lstrip('#')
            rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        else:
            rgb = color
        luminance = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255
        return luminance > 0.5

    def _lighten_color(self, color, factor=0.2):
        """Aclara un color"""
        from colorsys import rgb_to_hls, hls_to_rgb
        if color.startswith('#'):
            color = color.lstrip('#')
            rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        else:
            rgb = color
        h, l, s = rgb_to_hls(rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0)
        l = min(1.0, l + factor)
        r, g, b = hls_to_rgb(h, l, s)
        return f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'

    def _actualizar_botones_pendientes(self):
        """Actualiza la visibilidad de botones de pendientes según licencia"""
        # Limpiar frame
        for widget in self.pendientes_btn_frame.winfo_children():
            widget.destroy()

        if self.controller.licencia_controller.puede_ver_pendientes:
            # Botón VER PENDIENTES
            btn_pendientes = tk.Button(self.pendientes_btn_frame,
                    text="📋 PENDIENTES",
                    bg=self.theme.colores.get("pendiente", "#FFA500"),
                    fg=self.theme.colores["negro"],
                    font=("Segoe UI", 9, "bold"),
                    relief="flat",
                    padx=8,
                    pady=3,
                    cursor="hand2",
                    command=self._on_ver_pendientes)
            btn_pendientes.pack(side="left", padx=2)

            # Botón OCULTAR/MOSTRAR
            btn_text = "👁️ OCULTAR" if not self.ocultar_pendientes_var.get() else "👁️ MOSTRAR"
            btn_color = self.theme.colores["card"] if not self.ocultar_pendientes_var.get() else self.theme.colores["success"]
            
            btn_ocultar = tk.Button(self.pendientes_btn_frame,
                    text=btn_text,
                    bg=btn_color,
                    fg=self.theme.colores["texto"],
                    font=("Segoe UI", 9),
                    relief="flat",
                    padx=8,
                    pady=3,
                    cursor="hand2",
                    command=self._toggle_ocultar_pendientes)
            btn_ocultar.pack(side="left", padx=2)

            self.pendientes_btn_frame.pack(side="right", padx=2)
        else:
            self.pendientes_btn_frame.pack_forget()

    def _toggle_ocultar_pendientes(self):
        """Alterna la visualización de fallas pendientes"""
        self.ocultar_pendientes_var.set(not self.ocultar_pendientes_var.get())
        self._actualizar_botones_pendientes()
        self.actualizar_tabla()

    def _crear_tabla_principal(self):
        """Crea la tabla principal de fallas activas"""
        # Limpiar frame
        for widget in self.frame_tabla.winfo_children():
            widget.destroy()

        tree_frame = tk.Frame(self.frame_tabla, bg=self.theme.colores["fondo"])
        tree_frame.pack(fill="both", expand=True)

        columnas = ("#", "Máquina", "Tipo", "Inicio", "Proceso", "Fin", "Estado", "Nota")
        anchos = [60, 100, 120, 100, 100, 100, 100, 80]

        self.treeview_principal = ttk.Treeview(
            tree_frame, 
            columns=columnas, 
            show="headings", 
            style="Treeview"
        )

        for col, ancho in zip(columnas, anchos):
            self.treeview_principal.heading(col, text=col)
            self.treeview_principal.column(col, width=ancho, anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", 
                                 command=self.treeview_principal.yview)
        self.treeview_principal.configure(yscrollcommand=scrollbar.set)

        self.treeview_principal.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.treeview_principal.item_data = {}
        self.treeview_principal.bind("<Double-1>", self._on_doble_click)

    def actualizar_tabla(self):
        """Actualiza la tabla con las fallas activas actuales"""
        if not hasattr(self, 'treeview_principal') or not self.treeview_principal.winfo_exists():
            return

        # Determinar qué fallas mostrar
        fallas_a_mostrar = self.falla_controller.fallas_activas
        if self.ocultar_pendientes_var.get():
            fallas_a_mostrar = [a for a in fallas_a_mostrar 
                               if a.get("estado") != "pendiente"]

        # Actualizar contador
        if self.contador_fallas:
            self.contador_fallas.config(text=f"{len(fallas_a_mostrar)} activas")

        # Limpiar tabla
        for item in self.treeview_principal.get_children():
            self.treeview_principal.delete(item)
        self.treeview_principal.item_data.clear()

        if not fallas_a_mostrar:
            return

        # Configurar tags de color
        tipos_unicos = set([a["tipo"] for a in fallas_a_mostrar])
        for tipo in tipos_unicos:
            color = self.theme.get_color_para_tipo(tipo)
            self.treeview_principal.tag_configure(
                tipo,
                background=color,
                foreground="#000000" if is_light_color(color) else "#FFFFFF",
                font=("Segoe UI", 10, "bold")
            )

        self.treeview_principal.tag_configure(
            "pendiente", 
            background=self.theme.colores.get("pendiente", "#FFA500")
        )

        # Insertar datos
        for idx, alerta in enumerate(fallas_a_mostrar, 1):
            valores = self._obtener_valores_falla(alerta, idx)
            tags = [alerta["tipo"]]
            if alerta.get("estado") == "pendiente":
                tags.append("pendiente")
            
            item_id = self.treeview_principal.insert("", "end", values=valores, tags=tags)
            self.treeview_principal.item_data[item_id] = alerta

    def _obtener_valores_falla(self, alerta, idx):
        """Obtiene los valores formateados de una falla"""
        numero = alerta.get("numero_falla", idx)
        
        estado_guardado = alerta.get("estado", "activa")
        if estado_guardado == "pendiente":
            estado = "🟠 Pendiente"
        elif estado_guardado == "en_proceso":
            estado = "🟡 En Proceso"
        elif estado_guardado == "resuelta":
            estado = "✅ Resuelta"
        else:
            estado = "🔴 Activa"

        tiene_nota = "📝" if "nota_pendiente" in alerta and alerta["nota_pendiente"] else ""

        return (
            f"#{numero}",
            alerta["maquina"],
            alerta["tipo"],
            solo_hora(alerta.get("inicio", "")),
            solo_hora(alerta.get("proceso", "")),
            solo_hora(alerta.get("fin", "")),
            estado,
            tiene_nota
        )

    def update_stats(self):
        """Actualiza las estadísticas en tiempo real (sin recrear widgets)"""
        if not self.stats_container or not self.stats_container.winfo_exists():
            return

        # Obtener estadísticas reales
        stats = self.falla_controller.get_estadisticas()
        
        # Obtener datos de la BD
        resueltas_hoy = self._get_resueltas_hoy()
        tiempo_promedio = self._get_tiempo_promedio()
        
        # Si no hay widgets creados aún, crearlos
        if not hasattr(self, 'stats_widgets') or not self.stats_widgets:
            self._crear_widgets_estadisticas()
        
        # Actualizar los valores existentes
        try:
            # Actualizar Fallas Activas
            self.stats_widgets["activas"].config(text=str(stats["activas"]))
            
            # Actualizar En Proceso
            self.stats_widgets["en_proceso"].config(text=str(stats["en_proceso"]))
            
            # Actualizar Resueltas Hoy
            self.stats_widgets["resueltas_hoy"].config(text=str(resueltas_hoy))
            
            # Actualizar Tiempo Promedio
            self.stats_widgets["tiempo_promedio"].config(text=f"{tiempo_promedio:.1f} min")
            
            # Actualizar contador de fallas
            if self.contador_fallas and self.contador_fallas.winfo_exists():
                self.contador_fallas.config(text=f"{stats['activas']} activas")
                
        except Exception as e:
            print(f"Error actualizando estadísticas: {e}")
            # Si hay error, recrear widgets
            self._crear_widgets_estadisticas()
            
    def _crear_widgets_estadisticas(self):
        """Crea los widgets de estadísticas por primera vez"""
        # Limpiar contenedor
        for widget in self.stats_container.winfo_children():
            widget.destroy()
        
        # Crear diccionario para almacenar referencias
        self.stats_widgets = {}
        
        # Obtener datos actuales
        stats = self.falla_controller.get_estadisticas()
        resueltas_hoy = self._get_resueltas_hoy()
        tiempo_promedio = self._get_tiempo_promedio()
        
        # Definir las estadísticas
        stat_items = [
            ("activas", "Fallas Activas", stats["activas"]),
            ("en_proceso", "En Proceso", stats["en_proceso"]),
            ("resueltas_hoy", "Resueltas Hoy", resueltas_hoy),
            ("tiempo_promedio", "Tiempo Promedio", f"{tiempo_promedio:.1f} min")
        ]
        
        for key, label, value in stat_items:
            card = tk.Frame(
                self.stats_container,
                bg=lighten_color(self.theme.colores["card"], -0.1),
                relief="flat",
                borderwidth=1,
                highlightbackground=self.theme.colores["texto_secundario"]
            )
            card.pack(side="left", fill="both", expand=True, padx=5)
            
            # Valor (se actualizará después)
            value_label = tk.Label(
                card,
                text=str(value),
                bg=lighten_color(self.theme.colores["card"], -0.1),
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 18, "bold")
            )
            value_label.pack(pady=(15, 5))
            
            # Etiqueta
            tk.Label(
                card,
                text=label,
                bg=lighten_color(self.theme.colores["card"], -0.1),
                fg=self.theme.colores["texto_secundario"],
                font=("Segoe UI", 9)
            ).pack(pady=(0, 15))
            
            # Guardar referencia
            self.stats_widgets[key] = value_label
        
    def _get_resueltas_hoy(self) -> int:
        """Obtiene fallas resueltas hoy desde la BD"""
        try:
            conn = self.controller.db.get_connection()
            if not conn:
                print("No se pudo conectar a MySQL")
                return 0
            
            cursor = conn.cursor()
            hoy = datetime.now().strftime("%Y-%m-%d")
            cursor.execute("SELECT COUNT(*) FROM fallas WHERE DATE(fin) = %s", (hoy,))
            count = cursor.fetchone()[0] or 0
            cursor.close()
            conn.close()
            return count
        except Exception as e:
            print(f"Error obteniendo resueltas hoy: {e}")
            return 0

    def _get_tiempo_promedio(self) -> float:
        """Obtiene tiempo promedio de resolución desde la BD"""
        try:
            conn = self.controller.db.get_connection()
            if not conn:
                return 0
            
            cursor = conn.cursor()
            cursor.execute("""
                SELECT AVG(TIMESTAMPDIFF(MINUTE, inicio, fin))
                FROM fallas
                WHERE fin IS NOT NULL
            """)
            resultado = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            
            if resultado is not None:
                return float(resultado)
            return 0
        except Exception as e:
            print(f"Error obteniendo tiempo promedio: {e}")
            return 0

    def _on_registro_manual(self, tipo: str):
        """Maneja clic en botón de tipo de falla"""
        maquina = self.entrada_maquina.get().strip()
        if maquina:
            self.falla_controller.registrar_evento(maquina, tipo)
            self.actualizar_tabla()
            self.update_stats()
        else:
            messagebox.showwarning("Aviso", "Selecciona una máquina")

    def _on_doble_click(self, event):
        """Maneja doble clic en la tabla"""
        try:
            item = self.treeview_principal.selection()[0]
            alerta = self.treeview_principal.item_data.get(item)
            if alerta:
                self._mostrar_menu_contexto(event, alerta)
        except IndexError:
            pass

    def _mostrar_menu_contexto(self, event, alerta):
        """Muestra menú contextual para una falla"""
        menu = tk.Menu(self, tearoff=0, bg=self.theme.colores["card"], 
                      fg=self.theme.colores["texto"])
        
        estado = alerta.get("estado", "activa")
        licencia = self.controller.licencia_controller

        # Opción ver nota si existe
        if "nota_pendiente" in alerta and alerta["nota_pendiente"]:
            menu.add_command(label="📋 Ver Nota", 
                           command=lambda: self._mostrar_nota(alerta))

        # Opción agregar/editar nota (solo PRO)
        if licencia.puede_agregar_notas:
            if "nota_pendiente" in alerta and alerta["nota_pendiente"]:
                menu.add_command(label="✏️ Editar Nota", 
                               command=lambda: self._editar_nota(alerta))
            else:
                menu.add_command(label="📝 Agregar Nota", 
                               command=lambda: self._editar_nota(alerta))

        # Opciones según estado
        if estado == "activa":
            if menu.index("end") is not None:
                menu.add_separator()
            menu.add_command(label="🟡 Marcar en Proceso", 
                           command=lambda: self.falla_controller.marcar_en_proceso(alerta))

        elif estado == "en_proceso":
            if menu.index("end") is not None:
                menu.add_separator()
            
            if licencia.puede_usar_pendientes:
                menu.add_command(label="🟠 Marcar como Pendiente", 
                               command=lambda: self._marcar_pendiente(alerta))
            
            menu.add_command(label="✅ Finalizar Falla", 
                           command=lambda: self.falla_controller.finalizar_falla(alerta))

        elif estado == "pendiente":
            if menu.index("end") is not None:
                menu.add_separator()
            menu.add_command(label="✅ Resolver Pendiente",  # <-- Agregar emoji ✅
                        command=lambda: self.falla_controller.finalizar_falla(alerta))

        if menu.index("end") is not None:
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()
                
    def _mostrar_nota_pendiente(self, alerta):
        """Muestra la nota completa de una falla pendiente"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Nota de Falla Pendiente")
        dialog.geometry("500x400")
        dialog.configure(bg=self.theme.colores["fondo"])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Centrar
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (500 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (400 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        tk.Label(dialog,
                text="📋 Detalle de Falla Pendiente",
                bg=self.theme.colores["fondo"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 16, "bold")).pack(pady=20)
        
        info_frame = tk.Frame(dialog, bg=self.theme.colores["card"])
        info_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(info_frame,
                text=f"Máquina: {alerta['maquina']}",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=10, pady=5)
        
        tk.Label(info_frame,
                text=f"Tipo: {alerta['tipo']}",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 11)).pack(anchor="w", padx=10, pady=5)
        
        if "fecha_pendiente" in alerta:
            tk.Label(info_frame,
                    text=f"Fecha: {alerta['fecha_pendiente']}",
                    bg=self.theme.colores["card"],
                    fg=self.theme.colores["texto_secundario"],
                    font=("Segoe UI", 10)).pack(anchor="w", padx=10, pady=5)
        
        tk.Label(dialog,
                text="Nota:",
                bg=self.theme.colores["fondo"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 11, "bold")).pack(pady=(20, 5))
        
        texto_nota = tk.Text(dialog,
                            height=8,
                            width=50,
                            bg=self.theme.colores.get("superficie3", "#2d3047"),
                            fg=self.theme.colores["texto"],
                            font=("Segoe UI", 10),
                            wrap="word")
        texto_nota.pack(padx=20, pady=5)
        texto_nota.insert("1.0", alerta["nota_pendiente"])
        texto_nota.config(state="disabled")
        
        btn_frame = tk.Frame(dialog, bg=self.theme.colores["fondo"])
        btn_frame.pack(pady=20)
        
        def resolver():
            dialog.destroy()
            self.falla_controller.finalizar_falla(alerta)
        
        tk.Button(btn_frame,
                text="✅ Marcar como Resuelta",
                bg=self.theme.colores["success"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 10, "bold"),
                relief="flat",
                padx=15,
                pady=8,
                cursor="hand2",
                command=resolver).pack(side="left", padx=5)
        
        tk.Button(btn_frame,
                text="✏️ Editar Nota",
                bg=self.theme.colores["warning"],
                fg=self.theme.colores["negro"],
                font=("Segoe UI", 10),
                relief="flat",
                padx=15,
                pady=8,
                cursor="hand2",
                command=lambda: [dialog.destroy(), self._editar_nota(alerta)]).pack(side="left", padx=5)
        
        tk.Button(btn_frame,
                text="❌ Cerrar",
                bg=self.theme.colores["danger"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 10),
                relief="flat",
                padx=15,
                pady=8,
                cursor="hand2",
                command=dialog.destroy).pack(side="left", padx=5)

    def _mostrar_nota(self, alerta):
        """Muestra la nota de una falla"""
        if alerta.get("estado") == "pendiente":
            self._mostrar_nota_pendiente(alerta)
        else:
            messagebox.showinfo("Nota de Falla",
                            f"Máquina: {alerta['maquina']}\n"
                            f"Tipo: {alerta['tipo']}\n\n"
                            f"Nota:\n{alerta.get('nota_pendiente', '')}")

    def _editar_nota(self, alerta):
        """Abre diálogo para editar nota"""
        self._mostrar_dialogo_nota(alerta)

    def _marcar_pendiente(self, alerta):
        """Marca una falla como pendiente"""
        if not self.controller.licencia_controller.puede_usar_pendientes:
            messagebox.showinfo("Acceso Restringido",
                            "Las fallas pendientes son una característica\n"
                            "disponible solo en licencias MID y PRO.",
                            parent=self.root)
            return
        
        # Crear diálogo para la nota
        self._mostrar_dialogo_nota_pendiente(alerta)
        
    def _mostrar_dialogo_nota_pendiente(self, alerta):
        """Muestra un diálogo para agregar nota a una falla pendiente"""
        # Obtener la ventana raíz
        root_window = self.root
        
        dialog = tk.Toplevel(root_window)
        dialog.title("Nota de Falla Pendiente")
        dialog.geometry("500x450")
        dialog.configure(bg=self.theme.colores["fondo"])
        dialog.transient(root_window)
        dialog.grab_set()
        
        # Centrar diálogo
        dialog.update_idletasks()
        x = root_window.winfo_x() + (root_window.winfo_width() // 2) - (500 // 2)
        y = root_window.winfo_y() + (root_window.winfo_height() // 2) - (450 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Título
        tk.Label(dialog,
                text="📝 Marcar como Pendiente",
                bg=self.theme.colores["fondo"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 16, "bold")).pack(pady=20)
        
        # Información de la falla
        info_frame = tk.Frame(dialog, bg=self.theme.colores["card"])
        info_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(info_frame,
                text=f"Máquina: {alerta['maquina']}",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=10, pady=5)
        
        tk.Label(info_frame,
                text=f"Tipo: {alerta['tipo']}",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 11)).pack(anchor="w", padx=10, pady=5)
        
        # Área de nota
        tk.Label(dialog,
                text="Nota / Motivo del pendiente:",
                bg=self.theme.colores["fondo"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 11, "bold")).pack(pady=(20, 5))
        
        texto_nota = tk.Text(dialog,
                            height=8,
                            width=50,
                            bg=self.theme.colores.get("superficie3", "#2d3047"),
                            fg=self.theme.colores["texto"],
                            font=("Segoe UI", 10),
                            wrap="word")
        texto_nota.pack(padx=20, pady=5)
        
        # Si ya existe una nota, mostrarla
        if "nota_pendiente" in alerta and alerta["nota_pendiente"]:
            texto_nota.insert("1.0", alerta["nota_pendiente"])
        
        # Frame para botones
        btn_frame = tk.Frame(dialog, bg=self.theme.colores["fondo"])
        btn_frame.pack(pady=20)
        
        def guardar_nota():
            nota = texto_nota.get("1.0", tk.END).strip()
            if nota:
                # Actualizar la falla
                alerta["nota_pendiente"] = nota
                alerta["estado"] = "pendiente"
                alerta["fecha_pendiente"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Guardar en BD
                self.falla_controller.falla_model.guardar_falla_activa(alerta)
                
                # Actualizar vistas
                self.actualizar_tabla()
                self.update_stats()
                
                # Actualizar proyección si está abierta
                if hasattr(self.controller, 'main_view') and self.controller.main_view:
                    if hasattr(self.controller.main_view, 'proyeccion_view'):
                        self.controller.main_view.proyeccion_view._actualizar_tabla()
                
                dialog.destroy()
                messagebox.showinfo("✅ Nota Guardada", 
                                "La falla ha sido marcada como pendiente.",
                                parent=root_window)
            else:
                messagebox.showwarning("Aviso", 
                                    "Debes agregar una nota explicativa.", 
                                    parent=dialog)
        
        tk.Button(btn_frame,
                text="💾 Guardar y Marcar Pendiente",
                bg=self.theme.colores["warning"],
                fg=self.theme.colores["negro"],
                font=("Segoe UI", 11, "bold"),
                relief="flat",
                padx=20,
                pady=8,
                cursor="hand2",
                command=guardar_nota).pack(side="left", padx=5)
        
        tk.Button(btn_frame,
                text="❌ Cancelar",
                bg=self.theme.colores["danger"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 11),
                relief="flat",
                padx=20,
                pady=8,
                cursor="hand2",
                command=dialog.destroy).pack(side="left", padx=5)
        
    def _mostrar_dialogo_nota(self, alerta):
        """Muestra un diálogo para agregar/editar nota a cualquier falla (solo PRO)"""
        if not self.controller.licencia_controller.puede_agregar_notas:
            messagebox.showinfo("Acceso Restringido",
                            "Agregar notas solo está disponible\n"
                            "en licencias PRO.",
                            parent=self.root)
            return
        
        root_window = self.root
        
        dialog = tk.Toplevel(root_window)
        dialog.title("Nota de Falla")
        dialog.geometry("500x450")
        dialog.configure(bg=self.theme.colores["fondo"])
        dialog.transient(root_window)
        dialog.grab_set()
        
        # Centrar diálogo
        dialog.update_idletasks()
        x = root_window.winfo_x() + (root_window.winfo_width() // 2) - (500 // 2)
        y = root_window.winfo_y() + (root_window.winfo_height() // 2) - (450 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Título
        tk.Label(dialog,
                text="📝 Agregar/Editar Nota",
                bg=self.theme.colores["fondo"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 16, "bold")).pack(pady=20)
        
        # Información de la falla
        info_frame = tk.Frame(dialog, bg=self.theme.colores["card"])
        info_frame.pack(fill="x", padx=20, pady=10)
        
        estado_text = ""
        if alerta.get("estado") == "pendiente":
            estado_text = " (Pendiente)"
        
        tk.Label(info_frame,
                text=f"Máquina: {alerta['maquina']}{estado_text}",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=10, pady=5)
        
        tk.Label(info_frame,
                text=f"Tipo: {alerta['tipo']}",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 11)).pack(anchor="w", padx=10, pady=5)
        
        # Área de nota
        tk.Label(dialog,
                text="Nota:",
                bg=self.theme.colores["fondo"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 11, "bold")).pack(pady=(20, 5))
        
        texto_nota = tk.Text(dialog,
                            height=8,
                            width=50,
                            bg=self.theme.colores.get("superficie3", "#2d3047"),
                            fg=self.theme.colores["texto"],
                            font=("Segoe UI", 10),
                            wrap="word")
        texto_nota.pack(padx=20, pady=5)
        
        # Si ya existe una nota, mostrarla
        if "nota_pendiente" in alerta and alerta["nota_pendiente"]:
            texto_nota.insert("1.0", alerta["nota_pendiente"])
        
        # Frame para botones
        btn_frame = tk.Frame(dialog, bg=self.theme.colores["fondo"])
        btn_frame.pack(pady=20)
        
        def guardar_nota():
            nota = texto_nota.get("1.0", tk.END).strip()
            if nota:
                alerta["nota_pendiente"] = nota
                # No cambiar el estado, solo agregar nota
                
                # Guardar en BD
                self.falla_controller.falla_model.guardar_falla_activa(alerta)
                
                # Actualizar vistas
                self.actualizar_tabla()
                self.update_stats()
                
                # Actualizar proyección si está abierta
                if hasattr(self.controller, 'main_view') and self.controller.main_view:
                    if hasattr(self.controller.main_view, 'proyeccion_view'):
                        self.controller.main_view.proyeccion_view._actualizar_tabla()
                
                dialog.destroy()
                messagebox.showinfo("✅ Nota Guardada", 
                                "Nota agregada correctamente.",
                                parent=root_window)
            else:
                messagebox.showwarning("Aviso", 
                                    "La nota no puede estar vacía.", 
                                    parent=dialog)
        
        tk.Button(btn_frame,
                text="💾 Guardar Nota",
                bg=self.theme.colores["success"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 11, "bold"),
                relief="flat",
                padx=20,
                pady=8,
                cursor="hand2",
                command=guardar_nota).pack(side="left", padx=5)
        
        tk.Button(btn_frame,
                text="❌ Cancelar",
                bg=self.theme.colores["danger"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 11),
                relief="flat",
                padx=20,
                pady=8,
                cursor="hand2",
                command=dialog.destroy).pack(side="left", padx=5)
    
    def _on_ver_pendientes(self):
        """Muestra ventana con fallas pendientes"""
        from src.views.pendientes_view import PendientesView
        PendientesView(self, self.controller, self.theme, self.falla_controller)

    def _on_cerrar_todas(self):
        """Cierra todas las fallas activas"""
        if not self.falla_controller.fallas_activas:
            messagebox.showinfo("Información", "No hay fallas activas para cerrar")
            return

        respuesta = messagebox.askyesno(
            "Confirmar",
            f"¿Cerrar todas las {len(self.falla_controller.fallas_activas)} fallas activas?"
        )

        if respuesta:
            self.falla_controller.cerrar_todas_fallas()
            messagebox.showinfo("Completado", "Todas las fallas cerradas")

    def _on_actualizar_manual(self):
        """Actualiza manualmente desde BD"""
        nuevas = self.falla_controller.falla_model.cargar_fallas_activas()
        self.falla_controller.fallas_activas = nuevas
        self.actualizar_tabla()
        self.update_stats()
        messagebox.showinfo("Actualizado", 
                          f"Se cargaron {len(nuevas)} fallas activas")

    def _reproducir_alarma(self):
        """Reproduce una alarma sonora"""
        threading.Thread(target=lambda: winsound.Beep(1500, 1000)).start()