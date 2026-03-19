# src/views/estadisticas_view.py

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from tkcalendar import DateEntry
from src.utils.widgets import ModernButton, ModernEntry, ModernCombobox
import logging

logger = logging.getLogger(__name__)

class EstadisticasView:
    """Ventana de estadísticas avanzadas"""
    
    def __init__(self, parent, controller, theme_service, falla_controller):
        self.parent = parent
        self.controller = controller
        self.theme = theme_service
        self.falla_controller = falla_controller
        
        self.ventana = tk.Toplevel(parent)
        self.ventana.title("Estadísticas Avanzadas")
        self.ventana.geometry("1000x800")
        self.ventana.configure(bg=self.theme.colores["fondo"])
        self.ventana.resizable(True, True)
        self.ventana.transient(parent)
        self.ventana.grab_set()
        
        # Centrar ventana
        self.ventana.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (1000 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (800 // 2)
        self.ventana.geometry(f"+{x}+{y}")
        
        # Variables para filtros
        self.stats_desde = None
        self.stats_hasta = None
        self.tendencia_dias_var = tk.StringVar(value="7")
        
        self._setup_ui()
        self._cargar_datos_iniciales()
        
    def _setup_ui(self):
        """Configura la interfaz de usuario"""
        # Frame superior con información
        top_frame = tk.Frame(self.ventana, bg=self.theme.colores["fondo"])
        top_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        db_info = f"📊 Estadísticas Avanzadas - MySQL ({self.controller.db_config['host']})"
        tk.Label(top_frame, text=db_info, 
                bg=self.theme.colores["fondo"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 18, "bold")).pack(anchor="w")
        
        # Filtros (solo para PRO)
        if self.controller.licencia_controller.puede_ajustar_periodo_estadisticas:
            self._crear_filtros(top_frame)
        
        # Notebook con pestañas
        self.notebook = ttk.Notebook(self.ventana)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Crear pestañas
        self.tab_resumen = tk.Frame(self.notebook, bg=self.theme.colores["fondo"])
        self.tab_tendencias = tk.Frame(self.notebook, bg=self.theme.colores["fondo"])
        self.tab_metricas = tk.Frame(self.notebook, bg=self.theme.colores["fondo"])
        self.tab_maquinas = tk.Frame(self.notebook, bg=self.theme.colores["fondo"])
        
        self.notebook.add(self.tab_resumen, text="📊 Resumen General")
        self.notebook.add(self.tab_tendencias, text="📈 Tendencias")
        self.notebook.add(self.tab_metricas, text="🔧 Métricas por Tipo")
        self.notebook.add(self.tab_maquinas, text="⚙️ Análisis de Máquinas")
        
    def _crear_filtros(self, parent):
        """Crea los filtros de fecha (solo PRO)"""
        filtros_frame = tk.Frame(parent, bg=self.theme.colores["card"], relief="flat", bd=1)
        filtros_frame.pack(fill="x", pady=10)
        
        tk.Label(filtros_frame, text="🔍 Filtrar por período:", 
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        periodo_frame = tk.Frame(filtros_frame, bg=self.theme.colores["card"])
        periodo_frame.pack(fill="x", padx=15, pady=5)
        
        tk.Label(periodo_frame, text="Desde:", 
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto_secundario"],
                font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))
        
        self.stats_desde = DateEntry(periodo_frame, date_pattern='yyyy-mm-dd', width=12,
                                    background=self.theme.colores["card"],
                                    foreground=self.theme.colores["texto"],
                                    borderwidth=0)
        self.stats_desde.pack(side="left", padx=(0, 20))
        
        tk.Label(periodo_frame, text="Hasta:", 
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto_secundario"],
                font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))
        
        self.stats_hasta = DateEntry(periodo_frame, date_pattern='yyyy-mm-dd', width=12,
                                    background=self.theme.colores["card"],
                                    foreground=self.theme.colores["texto"],
                                    borderwidth=0)
        self.stats_hasta.pack(side="left", padx=(0, 20))
        
        tk.Label(periodo_frame, text="Días tendencia:", 
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto_secundario"],
                font=("Segoe UI", 10)).pack(side="left", padx=(20, 5))
        
        spin = tk.Spinbox(periodo_frame, from_=1, to=90, textvariable=self.tendencia_dias_var,
                         width=5, bg=self.theme.colores.get("superficie3", "#2d3047"),
                         fg=self.theme.colores["texto"], font=("Segoe UI", 10))
        spin.pack(side="left")
        
        tk.Button(periodo_frame, text="🔄 Aplicar Filtros", 
                command=self._recargar_datos,
                bg=self.theme.colores["accento"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 10),
                relief="flat",
                padx=10,
                pady=2,
                cursor="hand2").pack(side="left", padx=20)
        
    def _cargar_datos_iniciales(self):
        """Carga los datos iniciales en todas las pestañas"""
        # Determinar período
        if self.controller.licencia_controller.puede_ajustar_periodo_estadisticas and self.stats_desde and self.stats_hasta:
            desde = self.stats_desde.get_date().strftime("%Y-%m-%d")
            hasta = self.stats_hasta.get_date().strftime("%Y-%m-%d")
            dias = int(self.tendencia_dias_var.get())
        else:
            desde = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            hasta = datetime.now().strftime("%Y-%m-%d")
            dias = 7
        
        self._mostrar_resumen(desde, hasta)
        self._mostrar_tendencias(dias)
        self._mostrar_metricas_tipo(desde, hasta)
        self._mostrar_analisis_maquinas(desde, hasta)
        
    def _recargar_datos(self):
        """Recarga los datos con los nuevos filtros"""
        desde = self.stats_desde.get_date().strftime("%Y-%m-%d")
        hasta = self.stats_hasta.get_date().strftime("%Y-%m-%d")
        dias = int(self.tendencia_dias_var.get())
        
        # Limpiar pestañas
        for widget in self.tab_resumen.winfo_children():
            widget.destroy()
        for widget in self.tab_tendencias.winfo_children():
            widget.destroy()
        for widget in self.tab_metricas.winfo_children():
            widget.destroy()
        for widget in self.tab_maquinas.winfo_children():
            widget.destroy()
        
        self._mostrar_resumen(desde, hasta)
        self._mostrar_tendencias(dias)
        self._mostrar_metricas_tipo(desde, hasta)
        self._mostrar_analisis_maquinas(desde, hasta)
        
    def _mostrar_resumen(self, desde, hasta):
        """Muestra el resumen general"""
        frame = self.tab_resumen
        
        # Obtener datos
        datos = self._obtener_resumen(desde, hasta)
        
        if not datos:
            tk.Label(frame, text="No hay datos disponibles",
                    bg=self.theme.colores["fondo"],
                    fg=self.theme.colores["texto_secundario"],
                    font=("Segoe UI", 14)).pack(pady=50)
            return
        
        main = tk.Frame(frame, bg=self.theme.colores["fondo"])
        main.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(main,
                text=f"📊 Resumen General de Fallas - Período: {desde} a {hasta}",
                bg=self.theme.colores["fondo"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 16, "bold")).pack(pady=(0, 30))
        
        # Grid de estadísticas
        stats_grid = tk.Frame(main, bg=self.theme.colores["fondo"])
        stats_grid.pack(fill="x")
        stats_grid.columnconfigure(0, weight=1)
        stats_grid.columnconfigure(1, weight=1)
        
        stat_items = [
            ("📊 Total de Fallas", datos["total"]),
            ("📅 Fallas Hoy", datos["hoy"]),
            ("🔧 Máquinas Afectadas", datos["maquinas"]),
            ("⏱️ Tiempo Promedio", f"{datos['tiempo_promedio']:.1f} min"),
        ]
        
        for i, (label, value) in enumerate(stat_items):
            row = i // 2
            col = i % 2
            
            card = tk.Frame(stats_grid, bg=self.theme.colores["card"], relief="ridge", bd=2)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            tk.Label(card,
                    text=label,
                    bg=self.theme.colores["card"],
                    fg=self.theme.colores["texto_secundario"],
                    font=("Segoe UI", 12)).pack(pady=(20, 10))
            
            tk.Label(card,
                    text=str(value),
                    bg=self.theme.colores["card"],
                    fg=self.theme.colores["accento"],
                    font=("Segoe UI", 24, "bold")).pack(pady=(0, 20))
        
        # Tipo más común
        if datos["tipo_comun"]:
            tipo_card = tk.Frame(main, bg=self.theme.colores["card"], relief="ridge", bd=2)
            tipo_card.pack(fill="x", padx=10, pady=20)
            
            tk.Label(tipo_card,
                    text="🏆 Tipo de Falla Más Común",
                    bg=self.theme.colores["card"],
                    fg=self.theme.colores["texto"],
                    font=("Segoe UI", 14, "bold")).pack(pady=(15, 10))
            
            tipo_frame = tk.Frame(tipo_card, bg=self.theme.colores["card"])
            tipo_frame.pack(pady=(0, 20))
            
            color = self.theme.get_color_para_tipo(datos["tipo_comun"])
            tk.Label(tipo_frame,
                    text=datos["tipo_comun"],
                    bg=color,
                    fg="#000000" if self._is_light(color) else "#FFFFFF",
                    font=("Segoe UI", 18, "bold"),
                    padx=30,
                    pady=10).pack(side="left", padx=10)
            
            tk.Label(tipo_frame,
                    text=f"({datos['cantidad_tipo_comun']} ocurrencias)",
                    bg=self.theme.colores["card"],
                    fg=self.theme.colores["texto_secundario"],
                    font=("Segoe UI", 14)).pack(side="left", padx=10)
                    
    def _mostrar_tendencias(self, dias):
        """Muestra las tendencias de los últimos N días"""
        frame = self.tab_tendencias
        
        datos = self._obtener_tendencias(dias)
        
        if not datos:
            tk.Label(frame, text="No hay datos de tendencias disponibles",
                    bg=self.theme.colores["fondo"],
                    fg=self.theme.colores["texto_secundario"],
                    font=("Segoe UI", 14)).pack(pady=50)
            return
        
        # Crear gráfica
        fig, ax = plt.subplots(figsize=(10, 6))
        fechas = [d[0][5:] for d in datos]  # Solo MM-DD
        valores = [d[1] for d in datos]
        
        ax.bar(fechas, valores, color=self.theme.colores["accento"])
        ax.set_title(f"Fallas en los Últimos {dias} Días", fontsize=14, fontweight='bold')
        ax.set_xlabel("Fecha")
        ax.set_ylabel("Número de Fallas")
        ax.tick_params(axis='x', rotation=45)
        
        for i, v in enumerate(valores):
            ax.text(i, v + 0.1, str(v), ha='center', va='bottom', fontweight='bold')
        
        canvas = FigureCanvasTkAgg(fig, frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=20)
        
    def _mostrar_metricas_tipo(self, desde, hasta):
        """Muestra métricas detalladas por tipo"""
        frame = self.tab_metricas
        
        tk.Label(frame,
                text="Métricas Detalladas por Tipo de Falla",
                bg=self.theme.colores["fondo"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 14, "bold")).pack(pady=20)
        
        # Canvas con scroll
        canvas = tk.Canvas(frame, bg=self.theme.colores["fondo"], highlightthickness=0)
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=self.theme.colores["fondo"])
        
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Obtener datos
        datos_por_tipo = self._obtener_metricas_tipo(desde, hasta)
        
        for tipo, datos in datos_por_tipo.items():
            self._crear_tarjeta_tipo(scrollable, tipo, datos)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def _crear_tarjeta_tipo(self, parent, tipo, datos):
        """Crea una tarjeta para un tipo de falla"""
        frame = tk.Frame(parent, bg=self.theme.colores["card"])
        frame.pack(fill="x", padx=20, pady=5)
        
        color = self.theme.get_color_para_tipo(tipo)
        
        tk.Label(frame,
                text=tipo,
                bg=color,
                fg="#000000" if self._is_light(color) else "#FFFFFF",
                font=("Segoe UI", 10, "bold"),
                width=15,
                anchor="center").pack(side="left", padx=10, pady=10)
        
        tk.Label(frame,
                text=f"Total: {datos['total']} | Tiempo Promedio: {datos['tiempo_promedio']:.1f} min",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 10)).pack(side="left", padx=10, pady=10)
        
    def _mostrar_analisis_maquinas(self, desde, hasta):
        """Muestra análisis detallado por máquina"""
        frame = self.tab_maquinas
        
        tk.Label(frame,
                text="Top 10 Máquinas con Más Fallas - Desglose por Tipo",
                bg=self.theme.colores["fondo"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 16, "bold")).pack(pady=(20, 30))
        
        # Canvas con scroll
        canvas = tk.Canvas(frame, bg=self.theme.colores["fondo"], highlightthickness=0)
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=self.theme.colores["fondo"])
        
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Obtener datos
        top_maquinas = self._obtener_top_maquinas(desde, hasta)
        
        for idx, (maquina, datos) in enumerate(top_maquinas.items(), 1):
            self._crear_tarjeta_maquina(scrollable, idx, maquina, datos)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Botón exportar
        tk.Button(frame,
                 text="📊 Exportar Análisis de Máquinas",
                 bg=self.theme.colores["accento"],
                 fg=self.theme.colores["texto"],
                 font=("Segoe UI", 11, "bold"),
                 relief="flat",
                 padx=20,
                 pady=10,
                 cursor="hand2",
                 command=lambda: self._exportar_analisis(desde, hasta)).pack(pady=20)
        
    def _crear_tarjeta_maquina(self, parent, idx, maquina, datos):
        """Crea una tarjeta para una máquina"""
        container = tk.Frame(parent, bg=self.theme.colores["card"], relief="ridge", bd=2)
        container.pack(fill="x", padx=20, pady=10)
        
        header = tk.Frame(container, bg=self.theme.colores["card"])
        header.pack(fill="x", padx=15, pady=10)
        
        tk.Label(header,
                text=f"#{idx} - Máquina {maquina}",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["accento"],
                font=("Segoe UI", 14, "bold")).pack(side="left")
        
        tk.Label(header,
                text=f"Total: {datos['total']} fallas",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["success"],
                font=("Segoe UI", 12, "bold")).pack(side="right")
        
        tk.Frame(container, bg=self.theme.colores["texto_secundario"], height=1).pack(fill="x", padx=15, pady=5)
        
        # Desglose por tipo
        desglose = tk.Frame(container, bg=self.theme.colores["card"])
        desglose.pack(fill="x", padx=25, pady=15)
        
        # Headers
        headers = tk.Frame(desglose, bg=self._darken(self.theme.colores["card"]))
        headers.pack(fill="x", pady=(0, 5))
        
        tk.Label(headers,
                text="Tipo de Falla",
                bg=self._darken(self.theme.colores["card"]),
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 10, "bold"),
                width=25,
                anchor="w").pack(side="left", padx=10, pady=5)
        
        tk.Label(headers,
                text="Cantidad",
                bg=self._darken(self.theme.colores["card"]),
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 10, "bold"),
                width=15,
                anchor="center").pack(side="left", padx=10, pady=5)
        
        tk.Label(headers,
                text="Porcentaje",
                bg=self._darken(self.theme.colores["card"]),
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 10, "bold"),
                width=15,
                anchor="center").pack(side="left", padx=10, pady=5)
        
        # Datos
        for tipo, cantidad in datos['tipos'].items():
            row = tk.Frame(desglose, bg=self.theme.colores["card"])
            row.pack(fill="x", pady=2)
            
            color = self.theme.get_color_para_tipo(tipo)
            
            # Indicador de color
            color_ind = tk.Frame(row, bg=color, width=15, height=15)
            color_ind.pack(side="left", padx=(5, 10))
            color_ind.pack_propagate(False)
            
            tk.Label(row,
                    text=tipo,
                    bg=self.theme.colores["card"],
                    fg=self.theme.colores["texto"],
                    font=("Segoe UI", 10),
                    width=23,
                    anchor="w").pack(side="left", padx=5)
            
            tk.Label(row,
                    text=str(cantidad),
                    bg=self.theme.colores["card"],
                    fg=self.theme.colores["texto"],
                    font=("Segoe UI", 10, "bold"),
                    width=15,
                    anchor="center").pack(side="left", padx=5)
            
            porcentaje = (cantidad / datos['total']) * 100
            tk.Label(row,
                    text=f"{porcentaje:.1f}%",
                    bg=self.theme.colores["card"],
                    fg=self.theme.colores["warning"],
                    font=("Segoe UI", 10),
                    width=15,
                    anchor="center").pack(side="left", padx=5)
            
            # Barra de progreso
            barra = tk.Frame(row, bg=self.theme.colores["fondo"], width=100, height=10)
            barra.pack(side="left", padx=10)
            barra.pack_propagate(False)
            
            progreso = tk.Frame(barra,
                               bg=color,
                               width=int(porcentaje),
                               height=10)
            progreso.pack(side="left")
            
    def _obtener_resumen(self, desde, hasta):
        """Obtiene datos de resumen desde MySQL"""
        try:
            conn = self.controller.db.get_connection()
            if not conn:
                return None
            
            cursor = conn.cursor()
            
            # Total de fallas
            cursor.execute("SELECT COUNT(*) FROM fallas WHERE DATE(inicio) BETWEEN %s AND %s", (desde, hasta))
            total = cursor.fetchone()[0] or 0
            
            # Fallas hoy
            hoy = datetime.now().strftime("%Y-%m-%d")
            cursor.execute("SELECT COUNT(*) FROM fallas WHERE DATE(inicio) = %s", (hoy,))
            hoy_count = cursor.fetchone()[0] or 0
            
            # Máquinas afectadas
            cursor.execute("SELECT COUNT(DISTINCT maquina) FROM fallas WHERE DATE(inicio) BETWEEN %s AND %s", (desde, hasta))
            maquinas = cursor.fetchone()[0] or 0
            
            # Tipo más común
            cursor.execute("""
                SELECT tipo, COUNT(*) as cantidad
                FROM fallas
                WHERE DATE(inicio) BETWEEN %s AND %s
                GROUP BY tipo
                ORDER BY cantidad DESC
                LIMIT 1
            """, (desde, hasta))
            tipo_row = cursor.fetchone()
            tipo_comun = tipo_row[0] if tipo_row else None
            cantidad_tipo = tipo_row[1] if tipo_row else 0
            
            # Tiempo promedio
            cursor.execute("""
                SELECT AVG(TIMESTAMPDIFF(MINUTE, inicio, fin))
                FROM fallas
                WHERE fin IS NOT NULL AND DATE(inicio) BETWEEN %s AND %s
            """, (desde, hasta))
            tiempo = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                "total": total,
                "hoy": hoy_count,
                "maquinas": maquinas,
                "tiempo_promedio": float(tiempo),
                "tipo_comun": tipo_comun,
                "cantidad_tipo_comun": cantidad_tipo
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo resumen: {e}")
            return None
            
    def _obtener_tendencias(self, dias):
        """Obtiene datos de tendencia"""
        try:
            conn = self.controller.db.get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor()
            datos = []
            
            for i in range(dias - 1, -1, -1):
                fecha = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                cursor.execute("SELECT COUNT(*) FROM fallas WHERE DATE(inicio) = %s", (fecha,))
                count = cursor.fetchone()[0] or 0
                datos.append((fecha, count))
            
            conn.close()
            return datos
            
        except Exception as e:
            logger.error(f"Error obteniendo tendencias: {e}")
            return []
            
    def _obtener_metricas_tipo(self, desde, hasta):
        """Obtiene métricas por tipo"""
        resultado = {}
        
        try:
            conn = self.controller.db.get_connection()
            if not conn:
                return resultado
            
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT tipo, COUNT(*) as total,
                       AVG(TIMESTAMPDIFF(MINUTE, inicio, fin)) as tiempo
                FROM fallas
                WHERE DATE(inicio) BETWEEN %s AND %s
                GROUP BY tipo
            """, (desde, hasta))
            
            rows = cursor.fetchall()
            conn.close()
            
            for row in rows:
                resultado[row['tipo']] = {
                    "total": row['total'],
                    "tiempo_promedio": float(row['tiempo'] or 0)
                }
            
        except Exception as e:
            logger.error(f"Error obteniendo métricas por tipo: {e}")
        
        return resultado
        
    def _obtener_top_maquinas(self, desde, hasta):
        """Obtiene top 10 máquinas con desglose"""
        resultado = {}
        
        try:
            conn = self.controller.db.get_connection()
            if not conn:
                return resultado
            
            cursor = conn.cursor(dictionary=True)
            
            # Obtener top 10 máquinas
            cursor.execute("""
                SELECT maquina, COUNT(*) as total
                FROM fallas
                WHERE DATE(inicio) BETWEEN %s AND %s
                GROUP BY maquina
                ORDER BY total DESC
                LIMIT 10
            """, (desde, hasta))
            
            maquinas = cursor.fetchall()
            
            for m in maquinas:
                maquina = m['maquina']
                resultado[maquina] = {
                    "total": m['total'],
                    "tipos": {}
                }
                
                # Obtener desglose por tipo para esta máquina
                cursor.execute("""
                    SELECT tipo, COUNT(*) as cantidad
                    FROM fallas
                    WHERE maquina = %s AND DATE(inicio) BETWEEN %s AND %s
                    GROUP BY tipo
                    ORDER BY cantidad DESC
                """, (maquina, desde, hasta))
                
                tipos = cursor.fetchall()
                for t in tipos:
                    resultado[maquina]["tipos"][t['tipo']] = t['cantidad']
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error obteniendo top máquinas: {e}")
        
        return resultado
        
    def _exportar_analisis(self, desde, hasta):
        """Exporta el análisis de máquinas a Excel"""
        from tkinter import filedialog
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            initialfile="analisis_maquinas.xlsx"
        )
        
        if not file_path:
            return
        
        try:
            import pandas as pd
            
            conn = self.controller.db.get_connection()
            if not conn:
                messagebox.showerror("Error", "No se pudo conectar a la BD")
                return
            
            # Resumen por máquina
            query_resumen = """
                SELECT maquina, COUNT(*) as total_fallas,
                       COUNT(DISTINCT tipo) as tipos_distintos,
                       MIN(DATE(inicio)) as primera_falla,
                       MAX(DATE(inicio)) as ultima_falla
                FROM fallas
                WHERE DATE(inicio) BETWEEN %s AND %s
                GROUP BY maquina
                ORDER BY total_fallas DESC
            """
            df_resumen = pd.read_sql_query(query_resumen, conn, params=(desde, hasta))
            
            # Detalle por tipo
            query_detalle = """
                SELECT maquina, tipo, COUNT(*) as cantidad,
                       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY maquina), 1) as porcentaje
                FROM fallas
                WHERE DATE(inicio) BETWEEN %s AND %s
                GROUP BY maquina, tipo
                ORDER BY maquina, cantidad DESC
            """
            df_detalle = pd.read_sql_query(query_detalle, conn, params=(desde, hasta))
            
            conn.close()
            
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df_resumen.to_excel(writer, sheet_name='Resumen por Máquina', index=False)
                df_detalle.to_excel(writer, sheet_name='Desglose por Tipo', index=False)
            
            messagebox.showinfo("✅ Éxito", f"Análisis exportado a:\n{file_path}")
            
        except Exception as e:
            logger.error(f"Error exportando análisis: {e}")
            messagebox.showerror("Error", f"No se pudo exportar: {str(e)}")
            
    def _is_light(self, color):
        """Determina si un color es claro"""
        if color.startswith('#'):
            color = color.lstrip('#')
            r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            return luminance > 0.5
        return False
        
    def _darken(self, color, factor=0.1):
        """Oscurece un color"""
        if color.startswith('#'):
            color = color.lstrip('#')
            r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
            r = int(r * (1 - factor))
            g = int(g * (1 - factor))
            b = int(b * (1 - factor))
            return f'#{r:02x}{g:02x}{b:02x}'
        return color