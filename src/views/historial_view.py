# src/views/historial_view.py

import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from datetime import datetime, timedelta
from src.utils.widgets import ModernButton, ModernEntry, ModernCombobox
from src.utils.helpers import is_light_color
import logging

logger = logging.getLogger(__name__)

class HistorialView(tk.Frame):
    """Vista de Historial de Fallas"""
    
    def __init__(self, parent, controller, theme_service, falla_controller):
        super().__init__(parent, bg=theme_service.colores["fondo"])
        self.controller = controller
        self.theme = theme_service
        self.falla_controller = falla_controller
        
        self.ultimos_resultados = []
        self.tipos_falla = []
        self._cargar_tipos()
        
        self._setup_ui()

    def _cargar_tipos(self):
        """Carga los tipos de falla"""
        tipos_data = self.falla_controller.falla_model.cargar_tipos_falla()
        self.tipos_falla = [t["nombre"] for t in tipos_data]

    def _setup_ui(self):
        """Configura la interfaz de usuario"""
        # ===== FILTROS =====
        filters_card = tk.Frame(self, bg=self.theme.colores["card"])
        filters_card.pack(fill="x", padx=20, pady=20)

        tk.Label(filters_card,
                text="Filtrar Historial",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=20, pady=(15, 10))

        filters_grid = tk.Frame(filters_card, bg=self.theme.colores["card"])
        filters_grid.pack(fill="x", padx=20, pady=(0, 20))

        # Fila 1: Máquina y Tipo
        row1 = tk.Frame(filters_grid, bg=self.theme.colores["card"])
        row1.pack(fill="x", pady=5)

        tk.Label(row1,
                text="Máquina:",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto_secundario"],
                font=("Segoe UI", 10)).grid(row=0, column=0, padx=(0, 10))

        self.filtro_maquina = ModernEntry(row1, theme_service=self.theme, width=15)
        self.filtro_maquina.grid(row=0, column=1, padx=(0, 30))

        tk.Label(row1,
                text="Tipo:",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto_secundario"],
                font=("Segoe UI", 10)).grid(row=0, column=2, padx=(0, 10))

        self.filtro_tipo = ModernCombobox(row1, theme_service=self.theme,
                                        values=[""] + self.tipos_falla, width=15)
        self.filtro_tipo.grid(row=0, column=3, padx=(0, 30))

        # Fila 2: Fechas
        row2 = tk.Frame(filters_grid, bg=self.theme.colores["card"])
        row2.pack(fill="x", pady=5)

        tk.Label(row2,
                text="Desde:",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto_secundario"],
                font=("Segoe UI", 10)).grid(row=0, column=0, padx=(0, 10))

        self.filtro_desde = DateEntry(row2, date_pattern='yyyy-mm-dd', width=15,
                                     background=self.theme.colores["card"],
                                     foreground=self.theme.colores["texto"],
                                     borderwidth=0)
        self.filtro_desde.grid(row=0, column=1, padx=(0, 30))

        tk.Label(row2,
                text="Hasta:",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto_secundario"],
                font=("Segoe UI", 10)).grid(row=0, column=2, padx=(0, 10))

        self.filtro_hasta = DateEntry(row2, date_pattern='yyyy-mm-dd', width=15,
                                     background=self.theme.colores["card"],
                                     foreground=self.theme.colores["texto"],
                                     borderwidth=0)
        self.filtro_hasta.grid(row=0, column=3, padx=(0, 30))

        # Fila 3: Estado
        estado_frame = tk.Frame(filters_grid, bg=self.theme.colores["card"])
        estado_frame.pack(fill="x", pady=5)

        tk.Label(estado_frame,
                text="Estado:",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto_secundario"],
                font=("Segoe UI", 10)).pack(side="left", padx=(0, 10))

        opciones_estado = ["", "Resuelta", "Fue Pendiente"]
        self.filtro_estado = ModernCombobox(estado_frame, theme_service=self.theme,
                                          values=opciones_estado, width=15)
        self.filtro_estado.pack(side="left", padx=(0, 30))

        # Botones de acción
        action_frame = tk.Frame(filters_card, bg=self.theme.colores["card"])
        action_frame.pack(fill="x", padx=20, pady=(0, 20))

        tk.Button(action_frame,
                 text="🔍 Buscar",
                 bg=self.theme.colores["success"],
                 fg=self.theme.colores["texto"],
                 font=("Segoe UI", 10, "bold"),
                 relief="flat",
                 padx=15,
                 pady=5,
                 cursor="hand2",
                 command=self._buscar).pack(side="left", padx=5)

        tk.Button(action_frame,
                 text="📊 Ver Gráficas",
                 bg=self.theme.colores["accento"],
                 fg=self.theme.colores["texto"],
                 font=("Segoe UI", 10, "bold"),
                 relief="flat",
                 padx=15,
                 pady=5,
                 cursor="hand2",
                 command=self._ver_graficas).pack(side="left", padx=5)

        tk.Button(action_frame,
                 text="📁 Exportar Excel",
                 bg=self.theme.colores["warning"],
                 fg=self.theme.colores["negro"],
                 font=("Segoe UI", 10, "bold"),
                 relief="flat",
                 padx=15,
                 pady=5,
                 cursor="hand2",
                 command=self._exportar_excel).pack(side="left", padx=5)

        # ===== TABLA DE RESULTADOS =====
        table_container = tk.Frame(self, bg=self.theme.colores["fondo"])
        table_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.frame_tabla = tk.Frame(table_container, bg=self.theme.colores["fondo"])
        self.frame_tabla.pack(fill="both", expand=True)

    def _buscar(self):
        """Ejecuta la búsqueda en el historial"""
        for widget in self.frame_tabla.winfo_children():
            widget.destroy()

        try:
            conn = self.controller.db.get_connection()
            if not conn:
                messagebox.showerror("Error", "No se pudo conectar a la base de datos")
                return

            cursor = conn.cursor(dictionary=True)

            query = "SELECT * FROM fallas WHERE 1=1"
            params = []

            if self.filtro_maquina.get():
                query += " AND maquina LIKE %s"
                params.append(f"%{self.filtro_maquina.get()}%")
            
            if self.filtro_tipo.get():
                query += " AND tipo = %s"
                params.append(self.filtro_tipo.get())
            
            if self.filtro_desde.get():
                query += " AND DATE(inicio) >= %s"
                params.append(self.filtro_desde.get_date().strftime("%Y-%m-%d"))
            
            if self.filtro_hasta.get():
                query += " AND DATE(fin) <= %s"
                params.append(self.filtro_hasta.get_date().strftime("%Y-%m-%d"))
            
            if self.filtro_estado.get():
                if self.filtro_estado.get() == "Fue Pendiente":
                    query += " AND fecha_pendiente IS NOT NULL"
                elif self.filtro_estado.get() == "Resuelta":
                    query += " AND estado = 'resuelta'"

            query += " ORDER BY inicio DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            self.ultimos_resultados = rows
            self._mostrar_resultados(rows)

        except Exception as e:
            logger.error(f"Error en búsqueda: {e}")
            messagebox.showerror("Error", f"Error al buscar: {str(e)}")

    def _mostrar_resultados(self, rows):
        """Muestra los resultados en una tabla"""
        tree_frame = tk.Frame(self.frame_tabla, bg=self.theme.colores["fondo"])
        tree_frame.pack(fill="both", expand=True)

        columnas = ("ID", "Máquina", "Tipo", "Inicio", "Proceso", "Fin",
                   "# Falla", "T. Inicio-Proceso", "T. Proceso-Fin", "T. Total")

        tree = ttk.Treeview(tree_frame, columns=columnas, show="headings", style="Treeview")

        anchos = [60, 80, 100, 120, 120, 120, 70, 120, 120, 120]
        for col, ancho in zip(columnas, anchos):
            tree.heading(col, text=col)
            tree.column(col, width=ancho, anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for row in rows:
            valores = (
                row.get('id', ''),
                row.get('maquina', ''),
                row.get('tipo', ''),
                self._formatear_fecha(row.get('inicio', '')),
                self._formatear_fecha(row.get('proceso', '')),
                self._formatear_fecha(row.get('fin', '')),
                f"#{row.get('numero_falla', '')}",
                row.get('t_inicio_proceso', ''),
                row.get('t_proceso_fin', ''),
                row.get('t_total', '')
            )
            tree.insert("", "end", values=valores)

        count_label = tk.Label(self.frame_tabla,
                              text=f"Se encontraron {len(rows)} registros",
                              bg=self.theme.colores["fondo"],
                              fg=self.theme.colores["texto_secundario"],
                              font=("Segoe UI", 10))
        count_label.pack(side="bottom", pady=5)

    def _formatear_fecha(self, fecha):
        """Formatea fecha para mostrar solo hora si es necesario"""
        if not fecha:
            return ""
        try:
            if len(str(fecha)) > 10:
                return str(fecha)[11:16]
            return str(fecha)
        except:
            return str(fecha)

    def _ver_graficas(self):
        """Muestra gráficas estilo mosaico con barra de herramientas de matplotlib"""
        if not self.ultimos_resultados:
            messagebox.showwarning("Aviso", "Primero realiza una búsqueda")
            return

        if not self.controller.licencia_controller.puede_ver_graficos:
            messagebox.showinfo("Acceso Restringido",
                              "Las gráficas requieren licencia MID o PRO")
            return

        # Seleccionar tipos a incluir (solo PRO)
        tipos_a_incluir = None
        if hasattr(self.controller.licencia_controller, 'puede_filtrar_tipos_graficas') and \
           self.controller.licencia_controller.puede_filtrar_tipos_graficas:
            tipos_a_incluir = self._seleccionar_tipos_para_graficas()
            if not tipos_a_incluir:
                return

        try:
            # Convertir a DataFrame
            if self.ultimos_resultados and isinstance(self.ultimos_resultados[0], dict):
                df = pd.DataFrame(self.ultimos_resultados)
            else:
                messagebox.showerror("Error", "Formato de datos incorrecto")
                return

            # Filtrar por tipos seleccionados
            if tipos_a_incluir and 'tipo' in df.columns:
                df = df[df['tipo'].isin(tipos_a_incluir)]
                if df.empty:
                    messagebox.showwarning("Sin datos", "No hay datos para los tipos seleccionados.")
                    return

            # Renombrar columnas para las gráficas
            column_mapping = {
                'tipo': 'Tipo',
                'maquina': 'Máquina',
                't_inicio_proceso': 'T. Inicio-Proceso',
                't_proceso_fin': 'T. Proceso-Fin',
                't_total': 'T. Total'
            }
            
            for old_col, new_col in column_mapping.items():
                if old_col in df.columns:
                    df.rename(columns={old_col: new_col}, inplace=True)

            # Crear ventana de gráficas
            graph_window = tk.Toplevel(self)
            graph_window.title("Análisis Completo de Fallas - Sistema Andon")
            graph_window.geometry("1200x900")
            graph_window.configure(bg=self.theme.colores["fondo"])

            # Centrar ventana
            graph_window.update_idletasks()
            x = self.winfo_toplevel().winfo_x() + (self.winfo_toplevel().winfo_width() // 2) - (1200 // 2)
            y = self.winfo_toplevel().winfo_y() + (self.winfo_toplevel().winfo_height() // 2) - (900 // 2)
            graph_window.geometry(f"+{x}+{y}")

            # Frame principal con scroll
            main_frame = tk.Frame(graph_window, bg=self.theme.colores["fondo"])
            main_frame.pack(fill="both", expand=True)

            # Canvas con scroll para manejar ventanas pequeñas
            canvas = tk.Canvas(main_frame, bg=self.theme.colores["fondo"], highlightthickness=0)
            scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg=self.theme.colores["fondo"])

            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            plt.style.use('seaborn-v0_8-darkgrid')
            
            # Crear figura con subplots en grid 2x3 (mosaico)
            fig, axes = plt.subplots(2, 3, figsize=(18, 12))
            fig.suptitle("Análisis Completo de Fallas - Sistema Andon", fontsize=16, fontweight='bold')

            if not df.empty:
                # ===== GRÁFICA 1: Fallas por Tipo =====
                if 'Tipo' in df.columns:
                    tipo_counts = df['Tipo'].value_counts()
                    if not tipo_counts.empty:
                        colores_tipos = [self.theme.get_color_para_tipo(t) for t in tipo_counts.index]
                        tipo_counts.plot(kind="bar", ax=axes[0, 0],
                                    title="Fallas por Tipo de Error",
                                    color=colores_tipos)
                        axes[0, 0].set_xlabel("Tipo de Error")
                        axes[0, 0].set_ylabel("Cantidad")
                        axes[0, 0].tick_params(axis='x', rotation=45)
                    else:
                        axes[0, 0].text(0.5, 0.5, "Sin datos para esta gráfica",
                                    ha='center', va='center', transform=axes[0, 0].transAxes)

                # ===== GRÁFICA 2: Fallas por Máquina =====
                if 'Máquina' in df.columns:
                    maquina_counts = df['Máquina'].value_counts()
                    if not maquina_counts.empty:
                        maquina_counts.plot(kind="bar", ax=axes[0, 1],
                                        title="Fallas por Máquina",
                                        color=self.theme.colores["accento"])
                        axes[0, 1].set_xlabel("Máquina")
                        axes[0, 1].set_ylabel("Cantidad")
                        axes[0, 1].tick_params(axis='x', rotation=45)

                # ===== GRÁFICA 3: Fallas por Tipo en cada Máquina =====
                try:
                    if 'Máquina' in df.columns and 'Tipo' in df.columns:
                        pivot = pd.pivot_table(df, index='Máquina', columns='Tipo',
                                            aggfunc='size', fill_value=0)
                        if not pivot.empty:
                            colores_apilados = [self.theme.get_color_para_tipo(c) for c in pivot.columns]
                            pivot.plot(kind="bar", stacked=True, ax=axes[0, 2],
                                    title="Fallas por Tipo en cada Máquina",
                                    color=colores_apilados)
                            axes[0, 2].set_xlabel("Máquina")
                            axes[0, 2].set_ylabel("Cantidad de Fallas")
                            axes[0, 2].tick_params(axis='x', rotation=45)
                            axes[0, 2].legend(title="Tipo", bbox_to_anchor=(1.05, 1), loc='upper left')
                except Exception as e:
                    logger.error(f"Error en gráfica 3: {e}")

                # ===== GRÁFICA 4: Tiempo Total Promedio por Tipo =====
                try:
                    if 'T. Total' in df.columns:
                        df['T. Total'] = df['T. Total'].astype(str)
                        df['T. Total'] = pd.to_timedelta(df['T. Total'].str.extract(r'(\d+:\d+:\d+)')[0])
                        if 'Tipo' in df.columns and not df['T. Total'].isna().all():
                            df_total = df.groupby("Tipo")["T. Total"].mean().dropna()
                            if not df_total.empty:
                                df_total_horas = df_total.dt.total_seconds() / 3600
                                colores_tiempo = [self.theme.get_color_para_tipo(t) for t in df_total_horas.index]
                                df_total_horas.plot(kind="bar", ax=axes[1, 0],
                                                title="Promedio del Tiempo Total por Tipo (horas)",
                                                color=colores_tiempo)
                                axes[1, 0].set_xlabel("Tipo")
                                axes[1, 0].set_ylabel("Horas Promedio")
                                axes[1, 0].tick_params(axis='x', rotation=45)
                except Exception as e:
                    logger.error(f"Error en gráfica 4: {e}")

                # ===== GRÁFICA 5: Promedio Inicio a Proceso =====
                try:
                    if 'T. Inicio-Proceso' in df.columns:
                        df['T. Inicio-Proceso'] = df['T. Inicio-Proceso'].astype(str)
                        df['T. Inicio-Proceso'] = pd.to_timedelta(df['T. Inicio-Proceso'].str.extract(r'(\d+:\d+:\d+)')[0])
                        if 'Tipo' in df.columns and not df['T. Inicio-Proceso'].isna().all():
                            df_ini_proc = df.groupby("Tipo")["T. Inicio-Proceso"].mean().dropna()
                            if not df_ini_proc.empty:
                                df_ini_proc_min = df_ini_proc.dt.total_seconds() / 60
                                colores_ini_proc = [self.theme.get_color_para_tipo(t) for t in df_ini_proc_min.index]
                                df_ini_proc_min.plot(kind="bar", ax=axes[1, 1],
                                                title="Promedio Inicio a Proceso (minutos)",
                                                color=colores_ini_proc)
                                axes[1, 1].set_xlabel("Tipo")
                                axes[1, 1].set_ylabel("Minutos Promedio")
                                axes[1, 1].tick_params(axis='x', rotation=45)
                except Exception as e:
                    logger.error(f"Error en gráfica 5: {e}")

                # ===== GRÁFICA 6: Promedio Proceso a Fin =====
                try:
                    if 'T. Proceso-Fin' in df.columns:
                        df['T. Proceso-Fin'] = df['T. Proceso-Fin'].astype(str)
                        df['T. Proceso-Fin'] = pd.to_timedelta(df['T. Proceso-Fin'].str.extract(r'(\d+:\d+:\d+)')[0])
                        if 'Tipo' in df.columns and not df['T. Proceso-Fin'].isna().all():
                            df_proc_fin = df.groupby("Tipo")["T. Proceso-Fin"].mean().dropna()
                            if not df_proc_fin.empty:
                                df_proc_fin_min = df_proc_fin.dt.total_seconds() / 60
                                colores_proc_fin = [self.theme.get_color_para_tipo(t) for t in df_proc_fin_min.index]
                                df_proc_fin_min.plot(kind="bar", ax=axes[1, 2],
                                                title="Promedio Proceso a Fin (minutos)",
                                                color=colores_proc_fin)
                                axes[1, 2].set_xlabel("Tipo")
                                axes[1, 2].set_ylabel("Minutos Promedio")
                                axes[1, 2].tick_params(axis='x', rotation=45)
                except Exception as e:
                    logger.error(f"Error en gráfica 6: {e}")

            else:
                for ax in axes.flat:
                    ax.text(0.5, 0.5, "No hay datos para mostrar",
                        ha='center', va='center', transform=ax.transAxes)

            plt.tight_layout()
            
            # Crear frame para la figura y su barra de herramientas
            fig_frame = tk.Frame(scrollable_frame, bg=self.theme.colores["fondo"])
            fig_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Embed la figura con barra de herramientas completa
            canvas_fig = FigureCanvasTkAgg(fig, fig_frame)
            canvas_fig.draw()
            
            # Barra de herramientas de matplotlib (tiene: inicio, zoom, mover, guardar, etc.)
            toolbar = NavigationToolbar2Tk(canvas_fig, fig_frame)
            toolbar.update()
            toolbar.pack(side=tk.TOP, fill=tk.X)
            
            canvas_fig.get_tk_widget().pack(fill="both", expand=True)
            
            plt.close(fig)

            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            # Botón cerrar
            btn_frame = tk.Frame(graph_window, bg=self.theme.colores["fondo"])
            btn_frame.pack(fill="x", padx=20, pady=10)
            
            tk.Button(btn_frame,
                     text="Cerrar",
                     command=graph_window.destroy,
                     bg=self.theme.colores["accento"],
                     fg=self.theme.colores["texto"],
                     font=("Segoe UI", 10),
                     padx=20,
                     pady=5).pack()

        except Exception as e:
            logger.error(f"Error al mostrar gráficas: {e}")
            messagebox.showerror("Error", f"No se pudieron generar las gráficas:\n{str(e)}")

    def _seleccionar_tipos_para_graficas(self):
        """Muestra un diálogo para seleccionar qué tipos incluir (solo PRO)"""
        dialog = tk.Toplevel(self)
        dialog.title("Seleccionar Tipos de Falla")
        dialog.geometry("400x500")
        dialog.configure(bg=self.theme.colores["fondo"])
        dialog.transient(self)
        dialog.grab_set()

        dialog.update_idletasks()
        x = self.winfo_toplevel().winfo_x() + (self.winfo_toplevel().winfo_width() // 2) - (400 // 2)
        y = self.winfo_toplevel().winfo_y() + (self.winfo_toplevel().winfo_height() // 2) - (500 // 2)
        dialog.geometry(f"+{x}+{y}")

        tk.Label(dialog, text="📊 Seleccionar Tipos de Falla", 
                bg=self.theme.colores["fondo"], fg=self.theme.colores["texto"], 
                font=("Segoe UI", 16, "bold")).pack(pady=20)

        canvas_frame = tk.Frame(dialog, bg=self.theme.colores["fondo"])
        canvas_frame.pack(fill="both", expand=True, padx=20, pady=10)

        canvas = tk.Canvas(canvas_frame, bg=self.theme.colores["fondo"], highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.theme.colores["fondo"])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        tipos_seleccionados_vars = {}
        
        tk.Label(scrollable_frame, text="Selecciona los tipos a incluir:", 
                bg=self.theme.colores["fondo"], fg=self.theme.colores["texto"], 
                font=("Segoe UI", 11)).pack(anchor="w", pady=(0, 10))

        for tipo in self.tipos_falla:
            var = tk.BooleanVar(value=True)
            tipos_seleccionados_vars[tipo] = var
            cb = tk.Checkbutton(scrollable_frame, text=tipo, variable=var,
                            bg=self.theme.colores["fondo"], fg=self.theme.colores["texto"],
                            selectcolor=self.theme.colores["accento"],
                            font=("Segoe UI", 10))
            cb.pack(anchor="w", pady=2)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        resultado = []

        def aceptar():
            nonlocal resultado
            resultado = [tipo for tipo, var in tipos_seleccionados_vars.items() if var.get()]
            if not resultado:
                messagebox.showwarning("Selección vacía", "Debes seleccionar al menos un tipo.", parent=dialog)
                return
            dialog.destroy()

        def seleccionar_todos():
            for var in tipos_seleccionados_vars.values():
                var.set(True)

        def seleccionar_nadie():
            for var in tipos_seleccionados_vars.values():
                var.set(False)

        btn_frame = tk.Frame(dialog, bg=self.theme.colores["fondo"])
        btn_frame.pack(fill="x", padx=20, pady=20)

        tk.Button(btn_frame, text="✅ Aceptar", command=aceptar,
                bg=self.theme.colores["success"], fg=self.theme.colores["texto"],
                font=("Segoe UI", 10, "bold"), relief="flat",
                padx=15, pady=5, cursor="hand2").pack(side="right", padx=5)

        tk.Button(btn_frame, text="❌ Cancelar", command=dialog.destroy,
                bg=self.theme.colores["danger"], fg=self.theme.colores["texto"],
                font=("Segoe UI", 10), relief="flat",
                padx=15, pady=5, cursor="hand2").pack(side="right", padx=5)

        tk.Button(btn_frame, text="✓ Todos", command=seleccionar_todos,
                bg=self.theme.colores["card"], fg=self.theme.colores["texto"],
                font=("Segoe UI", 9), relief="flat",
                padx=10, pady=3, cursor="hand2").pack(side="left", padx=5)

        tk.Button(btn_frame, text="✗ Ninguno", command=seleccionar_nadie,
                bg=self.theme.colores["card"], fg=self.theme.colores["texto"],
                font=("Segoe UI", 9), relief="flat",
                padx=10, pady=3, cursor="hand2").pack(side="left", padx=5)

        self.wait_window(dialog)
        return resultado if resultado else self.tipos_falla

    def _exportar_excel(self):
        """Exporta resultados a Excel con gráficas"""
        if not self.ultimos_resultados:
            messagebox.showwarning("Aviso", "Primero realiza una búsqueda")
            return

        from tkinter import filedialog
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")]
        )

        if not file_path:
            return

        licencia = self.controller.licencia_controller
        puede_graficas = licencia.puede_exportar_excel_con_graficos
        incluir_notas = licencia.puede_agregar_notas

        exito = self.controller.excel_service.exportar_excel_completo(
            self.ultimos_resultados,
            file_path,
            incluir_graficas=puede_graficas,
            incluir_notas=incluir_notas
        )

        if exito:
            messagebox.showinfo("✅ Éxito", f"Datos exportados a {file_path}")
            if licencia.excel_una_vez_dia:
                licencia.registrar_export_excel()
        else:
            messagebox.showerror("Error", "No se pudo exportar el archivo")

    def actualizar(self):
        """Actualiza la vista"""
        try:
            self._cargar_tipos()
            if hasattr(self, 'filtro_tipo') and self.filtro_tipo.winfo_exists():
                self.filtro_tipo['values'] = [""] + self.tipos_falla
        except Exception as e:
            logger.error(f"Error actualizando HistorialView: {e}")