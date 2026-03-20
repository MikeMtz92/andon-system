# src/views/historial_view.py

import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import pandas as pd
from datetime import datetime, timedelta
from src.utils.widgets import ModernButton, ModernEntry, ModernCombobox
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
        # Limpiar tabla anterior
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

            # Aplicar filtros
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

        # Contador de resultados
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
        """Muestra gráficas de los resultados"""
        if not self.ultimos_resultados:
            messagebox.showwarning("Aviso", "Primero realiza una búsqueda")
            return

        if not self.controller.licencia_controller.puede_ver_graficos:
            messagebox.showinfo("Acceso Restringido",
                              "Las gráficas requieren licencia MID o PRO")
            return

        # Aquí iría la lógica para mostrar gráficas
        # Por ahora, un placeholder
        messagebox.showinfo("Información", 
                          "Funcionalidad de gráficas en implementación")

    def _exportar_excel(self):
        """Exporta resultados a Excel"""
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

        # Verificar límites de licencia
        licencia = self.controller.licencia_controller
        puede_graficas = licencia.puede_exportar_excel_con_graficos
        incluir_notas = licencia.puede_agregar_notas

        # Usar el servicio de Excel
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
        """Actualiza la vista (llamado cuando cambian los datos)"""
        try:
            # Recargar tipos por si cambiaron
            self._cargar_tipos()
            if hasattr(self, 'filtro_tipo') and self.filtro_tipo.winfo_exists():
                self.filtro_tipo['values'] = [""] + self.tipos_falla
        except Exception as e:
            logger.error(f"Error actualizando HistorialView: {e}")