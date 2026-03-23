# src/views/estadisticas_view.py

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from tkcalendar import DateEntry
from src.utils.widgets import ModernFrame
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
        self.ventana.transient(parent)
        
        # Centrar
        self.ventana.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (1000 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (800 // 2)
        self.ventana.geometry(f"+{x}+{y}")
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Configura la interfaz de usuario"""
        # Header
        header = tk.Frame(self.ventana, bg=self.theme.colores["fondo"])
        header.pack(fill="x", padx=20, pady=(20, 10))
        
        tk.Label(header,
                text="📊 Estadísticas Avanzadas",
                bg=self.theme.colores["fondo"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 18, "bold")).pack(anchor="w")
        
        # Filtros (solo para PRO)
        if self.controller.licencia_controller.puede_ajustar_periodo_estadisticas:
            self._crear_filtros()
        
        # Notebook con pestañas
        self.notebook = ttk.Notebook(self.ventana)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Crear pestañas
        self.tab_resumen = tk.Frame(self.notebook, bg=self.theme.colores["fondo"])
        self.notebook.add(self.tab_resumen, text="📊 Resumen General")
        
        self.tab_tendencias = ModernFrame(self.notebook, theme_service=self.theme)
        self.notebook.add(self.tab_tendencias, text="📈 Tendencias")

        self.tab_metricas = ModernFrame(self.notebook, theme_service=self.theme)
        self.notebook.add(self.tab_metricas, text="🔧 Métricas por Tipo")

        self.tab_maquinas = ModernFrame(self.notebook, theme_service=self.theme)
        self.notebook.add(self.tab_maquinas, text="⚙️ Análisis de Máquinas")
        
        # Cargar datos iniciales
        self._recargar_datos()
        
    def _crear_filtros(self):
        """Crea los filtros de fecha (solo PRO)"""
        filtros_frame = tk.Frame(self.ventana, bg=self.theme.colores["card"], relief="flat", bd=1)
        filtros_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(filtros_frame,
                text="🔍 Filtrar por período:",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        periodo_frame = tk.Frame(filtros_frame, bg=self.theme.colores["card"])
        periodo_frame.pack(fill="x", padx=15, pady=5)
        
        tk.Label(periodo_frame,
                text="Desde:",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto_secundario"],
                font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))
        
        self.stats_desde = DateEntry(periodo_frame, date_pattern='yyyy-mm-dd', width=12,
                                    background=self.theme.colores["card"],
                                    foreground=self.theme.colores["texto"])
        self.stats_desde.pack(side="left", padx=(0, 20))
        
        tk.Label(periodo_frame,
                text="Hasta:",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto_secundario"],
                font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))
        
        self.stats_hasta = DateEntry(periodo_frame, date_pattern='yyyy-mm-dd', width=12,
                                    background=self.theme.colores["card"],
                                    foreground=self.theme.colores["texto"])
        self.stats_hasta.pack(side="left", padx=(0, 20))
        
        tk.Label(periodo_frame,
                text="Días tendencia:",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto_secundario"],
                font=("Segoe UI", 10)).pack(side="left", padx=(20, 5))
        
        self.tendencia_dias_var = tk.StringVar(value="7")
        tk.Spinbox(periodo_frame, from_=1, to=90, textvariable=self.tendencia_dias_var,
                  width=5, bg=self.theme.colores.get("superficie3", "#2d3047"),
                  fg=self.theme.colores["texto"], font=("Segoe UI", 10)).pack(side="left")
        
        tk.Button(periodo_frame,
                 text="🔄 Aplicar Filtros",
                 command=self._recargar_datos,
                 bg=self.theme.colores["accento"],
                 fg=self.theme.colores["texto"],
                 font=("Segoe UI", 10),
                 relief="flat",
                 padx=10,
                 pady=2,
                 cursor="hand2").pack(side="left", padx=20)
        
    def _recargar_datos(self):
        """Recarga los datos con los filtros actuales"""
        # Determinar período
        if hasattr(self, 'stats_desde') and hasattr(self, 'stats_hasta'):
            desde = self.stats_desde.get_date().strftime("%Y-%m-%d")
            hasta = self.stats_hasta.get_date().strftime("%Y-%m-%d")
            dias = int(self.tendencia_dias_var.get())
        else:
            # Valores por defecto (últimos 7 días)
            hasta = datetime.now().strftime("%Y-%m-%d")
            desde = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            dias = 7
        
        # Cargar cada pestaña
        self._mostrar_resumen(desde, hasta)
        self._mostrar_tendencias(dias)
        self._mostrar_metricas(desde, hasta)
        self._mostrar_analisis_maquinas(desde, hasta)
        
    def _mostrar_resumen(self, desde, hasta):
        """Muestra el resumen general"""
        # Limpiar pestaña
        for widget in self.tab_resumen.winfo_children():
            widget.destroy()
        
        # Obtener datos
        datos = self._obtener_resumen(desde, hasta)
        if not datos:
            tk.Label(self.tab_resumen,
                    text="No hay datos para el período seleccionado",
                    bg=self.theme.colores["fondo"],
                    fg=self.theme.colores["texto_secundario"],
                    font=("Segoe UI", 14)).pack(expand=True)
            return
        
        # Mostrar datos
        main = tk.Frame(self.tab_resumen, bg=self.theme.colores["fondo"])
        main.pack(fill="both", expand=True, padx=20, pady=20)
        
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
                fg="#000000" if self._is_light_color(color) else "#FFFFFF",
                font=("Segoe UI", 18, "bold"),
                padx=30,
                pady=10).pack(side="left", padx=10)
        
        tk.Label(tipo_frame,
                text=f"({datos['cantidad_tipo_comun']} ocurrencias)",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto_secundario"],
                font=("Segoe UI", 14)).pack(side="left", padx=10)
        
    def _mostrar_tendencias(self, dias):
        """Muestra gráfica de tendencias"""
        # Limpiar pestaña
        for widget in self.tab_tendencias.winfo_children():
            widget.destroy()
        
        # Obtener datos
        datos = self._obtener_tendencias(dias)
        if not datos:
            tk.Label(self.tab_tendencias,
                    text="No hay datos suficientes",
                    bg=self.theme.colores["fondo"],
                    fg=self.theme.colores["texto_secundario"],
                    font=("Segoe UI", 14)).pack(expand=True)
            return
        
        # Crear gráfica
        fig, ax = plt.subplots(figsize=(10, 6))
        fechas = [d[0][5:] for d in datos]
        valores = [d[1] for d in datos]
        
        ax.bar(fechas, valores, color=self.theme.colores["accento"])
        ax.set_title(f"Fallas en los Últimos {dias} Días", fontsize=14, fontweight='bold')
        ax.set_xlabel("Fecha")
        ax.set_ylabel("Número de Fallas")
        ax.tick_params(axis='x', rotation=45)
        
        for i, v in enumerate(valores):
            ax.text(i, v + 0.1, str(v), ha='center', va='bottom', fontweight='bold')
        
        canvas = FigureCanvasTkAgg(fig, self.tab_tendencias)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=20)
        
    def _mostrar_metricas(self, desde, hasta):
        """Muestra métricas por tipo"""
        # Limpiar pestaña
        for widget in self.tab_metricas.winfo_children():
            widget.destroy()
        
        tk.Label(self.tab_metricas,
                text="Métricas Detalladas por Tipo de Falla",
                bg=self.theme.colores["fondo"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 14, "bold")).pack(pady=20)
        
        # Canvas con scroll
        canvas = tk.Canvas(self.tab_metricas, bg=self.theme.colores["fondo"], highlightthickness=0)
        scrollbar = tk.Scrollbar(self.tab_metricas, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=self.theme.colores["fondo"])
        
        scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Obtener tipos
        tipos = self.falla_controller.falla_model.cargar_tipos_falla()
        
        for tipo in tipos:
            self._crear_tarjeta_tipo(scrollable, tipo["nombre"], desde, hasta)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def _crear_tarjeta_tipo(self, parent, tipo, desde, hasta):
        """Crea una tarjeta para un tipo de falla"""
        # Obtener estadísticas para este tipo
        conn = self.controller.db.get_connection()
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*), 
                       AVG(TIMESTAMPDIFF(MINUTE, inicio, fin))
                FROM fallas 
                WHERE tipo = %s AND DATE(inicio) BETWEEN %s AND %s
            """, (tipo, desde, hasta))
            total, promedio = cursor.fetchone()
            conn.close()
            
            if not total:
                return
            
            # Crear tarjeta
            card = tk.Frame(parent, bg=self.theme.colores["card"])
            card.pack(fill="x", padx=20, pady=5)
            
            color = self.theme.get_color_para_tipo(tipo)
            
            tk.Label(card,
                    text=tipo,
                    bg=color,
                    fg="#000000" if self._is_light_color(color) else "#FFFFFF",
                    font=("Segoe UI", 10, "bold"),
                    width=15,
                    anchor="center").pack(side="left", padx=10, pady=10)
            
            tiempo_text = f" | Tiempo Promedio: {promedio:.1f} min" if promedio else ""
            tk.Label(card,
                    text=f"Total: {total}{tiempo_text}",
                    bg=self.theme.colores["card"],
                    fg=self.theme.colores["texto"],
                    font=("Segoe UI", 10)).pack(side="left", padx=10, pady=10)
                    
        except Exception as e:
            logger.error(f"Error obteniendo métricas para {tipo}: {e}")
            if conn:
                conn.close()
        
    def _mostrar_analisis_maquinas(self, desde, hasta):
        """Muestra análisis de máquinas"""
        # Limpiar pestaña
        for widget in self.tab_maquinas.winfo_children():
            widget.destroy()
        
        canvas = tk.Canvas(self.tab_maquinas, bg=self.theme.colores["fondo"], highlightthickness=0)
        scrollbar = tk.Scrollbar(self.tab_maquinas, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=self.theme.colores["fondo"])
        
        scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        tk.Label(scrollable,
                text="Top 10 Máquinas con Más Fallas - Desglose por Tipo",
                bg=self.theme.colores["fondo"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 16, "bold")).pack(pady=(20, 30))
        
        # Obtener top máquinas
        conn = self.controller.db.get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT maquina, COUNT(*) as total
                    FROM fallas
                    WHERE DATE(inicio) BETWEEN %s AND %s
                    GROUP BY maquina
                    ORDER BY total DESC
                    LIMIT 10
                """, (desde, hasta))
                top_maquinas = cursor.fetchall()
                conn.close()
                
                for idx, (maquina, total) in enumerate(top_maquinas, 1):
                    self._crear_tarjeta_maquina(scrollable, idx, maquina, total, desde, hasta)
                    
            except Exception as e:
                logger.error(f"Error obteniendo top máquinas: {e}")
                if conn:
                    conn.close()
        
        # Botón exportar
        tk.Button(scrollable,
                 text="📊 Exportar Análisis de Máquinas",
                 bg=self.theme.colores["accento"],
                 fg=self.theme.colores["texto"],
                 font=("Segoe UI", 11, "bold"),
                 relief="flat",
                 padx=20,
                 pady=10,
                 cursor="hand2",
                 command=lambda: self._exportar_analisis(desde, hasta)).pack(pady=30)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def _crear_tarjeta_maquina(self, parent, idx, maquina, total, desde, hasta):
        """Crea una tarjeta para una máquina con desglose por tipo"""
        container = tk.Frame(parent, bg=self.theme.colores["card"], relief="ridge", bd=2)
        container.pack(fill="x", padx=20, pady=10)
        
        # Header
        header = tk.Frame(container, bg=self.theme.colores["card"])
        header.pack(fill="x", padx=15, pady=10)
        
        tk.Label(header,
                text=f"#{idx} - Máquina {maquina}",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["accento"],
                font=("Segoe UI", 14, "bold")).pack(side="left")
        
        tk.Label(header,
                text=f"Total: {total} fallas",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["success"],
                font=("Segoe UI", 12, "bold")).pack(side="right")
        
        tk.Frame(container, bg=self.theme.colores["texto_secundario"], height=1).pack(fill="x", padx=15, pady=5)
        
        # Obtener desglose por tipo
        conn = self.controller.db.get_connection()
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT tipo, COUNT(*) as cantidad
                FROM fallas
                WHERE maquina = %s AND DATE(inicio) BETWEEN %s AND %s
                GROUP BY tipo
                ORDER BY cantidad DESC
            """, (maquina, desde, hasta))
            tipos = cursor.fetchall()
            conn.close()
            
            # Mostrar desglose
            desglose = tk.Frame(container, bg=self.theme.colores["card"])
            desglose.pack(fill="x", padx=25, pady=15)
            
            for tipo, cantidad in tipos:
                row = tk.Frame(desglose, bg=self.theme.colores["card"])
                row.pack(fill="x", pady=2)
                
                color = self.theme.get_color_para_tipo(tipo)
                
                # Indicador de color
                indicador = tk.Frame(row, bg=color, width=15, height=15)
                indicador.pack(side="left", padx=(5, 10))
                indicador.pack_propagate(False)
                
                # Nombre del tipo
                tk.Label(row,
                        text=tipo,
                        bg=self.theme.colores["card"],
                        fg=self.theme.colores["texto"],
                        font=("Segoe UI", 10),
                        width=20,
                        anchor="w").pack(side="left", padx=5)
                
                # Cantidad
                tk.Label(row,
                        text=str(cantidad),
                        bg=self.theme.colores["card"],
                        fg=self.theme.colores["texto"],
                        font=("Segoe UI", 10, "bold"),
                        width=10,
                        anchor="center").pack(side="left", padx=5)
                
                # Porcentaje
                porcentaje = (cantidad / total) * 100
                tk.Label(row,
                        text=f"{porcentaje:.1f}%",
                        bg=self.theme.colores["card"],
                        fg=self.theme.colores["warning"],
                        font=("Segoe UI", 10),
                        width=10,
                        anchor="center").pack(side="left", padx=5)
                
                # Barra de progreso
                barra_frame = tk.Frame(row, bg=self.theme.colores["fondo"], width=100, height=10)
                barra_frame.pack(side="left", padx=10)
                barra_frame.pack_propagate(False)
                
                barra = tk.Frame(barra_frame,
                               bg=color,
                               width=int(porcentaje),
                               height=10)
                barra.pack(side="left")
                
        except Exception as e:
            logger.error(f"Error obteniendo desglose: {e}")
            if conn:
                conn.close()
        
    def _obtener_resumen(self, desde, hasta):
        """Obtiene datos de resumen desde la BD"""
        conn = self.controller.db.get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            
            # Total fallas en período
            cursor.execute("SELECT COUNT(*) FROM fallas WHERE DATE(inicio) BETWEEN %s AND %s",
                         (desde, hasta))
            total = cursor.fetchone()[0] or 0
            
            # Fallas hoy
            hoy = datetime.now().strftime("%Y-%m-%d")
            cursor.execute("SELECT COUNT(*) FROM fallas WHERE DATE(inicio) = %s", (hoy,))
            fallas_hoy = cursor.fetchone()[0] or 0
            
            # Máquinas afectadas
            cursor.execute("SELECT COUNT(DISTINCT maquina) FROM fallas WHERE DATE(inicio) BETWEEN %s AND %s",
                         (desde, hasta))
            maquinas = cursor.fetchone()[0] or 0
            
            # Tiempo promedio
            cursor.execute("""
                SELECT AVG(TIMESTAMPDIFF(MINUTE, inicio, fin))
                FROM fallas
                WHERE fin IS NOT NULL AND DATE(inicio) BETWEEN %s AND %s
            """, (desde, hasta))
            tiempo = cursor.fetchone()[0] or 0
            
            # Tipo más común
            cursor.execute("""
                SELECT tipo, COUNT(*) as cantidad
                FROM fallas
                WHERE DATE(inicio) BETWEEN %s AND %s
                GROUP BY tipo
                ORDER BY cantidad DESC
                LIMIT 1
            """, (desde, hasta))
            row = cursor.fetchone()
            tipo_comun = row[0] if row else "N/A"
            cantidad_tipo = row[1] if row else 0
            
            conn.close()
            
            return {
                "total": total,
                "hoy": fallas_hoy,
                "maquinas": maquinas,
                "tiempo_promedio": float(tiempo),
                "tipo_comun": tipo_comun,
                "cantidad_tipo_comun": cantidad_tipo
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo resumen: {e}")
            if conn:
                conn.close()
            return None
        
    def _obtener_tendencias(self, dias):
        """Obtiene datos de tendencia para los últimos N días"""
        conn = self.controller.db.get_connection()
        if not conn:
            return None
        
        try:
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
            if conn:
                conn.close()
            return None
        
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
            conn = self.controller.db.get_connection()
            if not conn:
                messagebox.showerror("Error", "No se pudo conectar a la base de datos")
                return
            
            # Resumen por máquina
            query_resumen = """
                SELECT
                    maquina,
                    COUNT(*) as total_fallas,
                    COUNT(DISTINCT tipo) as tipos_distintos,
                    MIN(DATE(inicio)) as primera_falla,
                    MAX(DATE(inicio)) as ultima_falla
                FROM fallas
                WHERE DATE(inicio) BETWEEN %s AND %s
                GROUP BY maquina
                ORDER BY total_fallas DESC
            """
            df_resumen = pd.read_sql_query(query_resumen, conn, params=[desde, hasta])
            
            # Detalle por tipo
            query_detalle = """
                SELECT
                    maquina,
                    tipo,
                    COUNT(*) as cantidad
                FROM fallas
                WHERE DATE(inicio) BETWEEN %s AND %s
                GROUP BY maquina, tipo
                ORDER BY maquina, cantidad DESC
            """
            df_detalle = pd.read_sql_query(query_detalle, conn, params=[desde, hasta])
            
            conn.close()
            
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df_resumen.to_excel(writer, sheet_name='Resumen por Máquina', index=False)
                df_detalle.to_excel(writer, sheet_name='Desglose por Tipo', index=False)
            
            messagebox.showinfo("✅ Éxito", f"Análisis exportado a:\n{file_path}")
            
        except Exception as e:
            logger.error(f"Error exportando análisis: {e}")
            messagebox.showerror("Error", f"No se pudo exportar: {str(e)}")
            
    def _is_light_color(self, color):
        """Determina si un color es claro"""
        if color.startswith('#'):
            color = color.lstrip('#')
            rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        else:
            rgb = color
        luminance = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255
        return luminance > 0.5