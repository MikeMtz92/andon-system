# src/services/excel_service.py

import pandas as pd
import matplotlib.pyplot as plt
from openpyxl import load_workbook
from openpyxl.drawing.image import Image as ExcelImage
import io
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class ExcelService:
    """Servicio para generar reportes Excel con gráficas"""
    
    def __init__(self, theme_service):
        self.theme = theme_service

    def exportar_excel_completo(self, datos: List[Dict], file_path: str, 
                                tipos_seleccionados: Optional[List[str]] = None,
                                incluir_graficas: bool = True,
                                incluir_notas: bool = False) -> bool:
        """Exporta datos a Excel con formato y gráficas"""
        try:
            if not datos:
                logger.warning("No hay datos para exportar")
                return False
            
            # Convertir a DataFrame
            if isinstance(datos[0], dict):
                df = pd.DataFrame(datos)
            else:
                logger.error("Formato de datos no soportado")
                return False

            # Filtrar por tipos si se especificó
            if tipos_seleccionados and 'tipo' in df.columns:
                df = df[df['tipo'].isin(tipos_seleccionados)]
                if df.empty:
                    logger.warning("No hay datos para los tipos seleccionados")
                    return False

            # Mapear columnas
            column_mapping = {
                'id': 'ID',
                'maquina': 'Máquina',
                'tipo': 'Tipo',
                'inicio': 'Inicio',
                'proceso': 'Proceso',
                'fin': 'Fin',
                'numero_falla': '# Falla',
                't_inicio_proceso': 'T. Inicio-Proceso',
                't_proceso_fin': 'T. Proceso-Fin',
                't_total': 'T. Total',
                'estado': 'Estado',
                'fecha_pendiente': 'Fecha Pendiente',
                'nota_pendiente': 'Nota'
            }
            
            for old, new in column_mapping.items():
                if old in df.columns:
                    df.rename(columns={old: new}, inplace=True)

            # Definir columnas a exportar
            columnas_base = ['ID', 'Máquina', 'Tipo', 'Inicio', 'Proceso', 'Fin', 
                           '# Falla', 'Estado', 'T. Inicio-Proceso', 'T. Proceso-Fin', 'T. Total']
            
            if 'Fecha Pendiente' in df.columns:
                columnas_base.append('Fecha Pendiente')
            
            if incluir_notas and 'Nota' in df.columns:
                columnas_base.append('Nota')
            elif incluir_notas:
                df['Nota'] = ""
                columnas_base.append('Nota')

            # Filtrar columnas existentes
            columnas_existentes = [col for col in columnas_base if col in df.columns]
            df = df[columnas_existentes]

            # Guardar Excel
            df.to_excel(file_path, index=False)
            
            # Agregar gráficas si se solicita
            if incluir_graficas:
                wb = load_workbook(file_path)
                self._agregar_todas_graficas(df, wb)
                wb.save(file_path)

            logger.info(f"Excel exportado a {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error exportando Excel: {e}")
            return False

    def _agregar_todas_graficas(self, df: pd.DataFrame, wb):
        """Agrega TODAS las gráficas al archivo Excel"""
        try:
            # ===== GRÁFICA 1: Fallas por Tipo =====
            self._agregar_grafica_fallas_por_tipo(df, wb)
            
            # ===== GRÁFICA 2: Fallas por Máquina =====
            self._agregar_grafica_fallas_por_maquina(df, wb)
            
            # ===== GRÁFICA 3: Fallas por Tipo en cada Máquina (stacked) =====
            self._agregar_grafica_fallas_por_tipo_y_maquina(df, wb)
            
            # ===== GRÁFICA 4: Tiempo Total Promedio por Tipo =====
            self._agregar_grafica_tiempo_total_promedio(df, wb)
            
            # ===== GRÁFICA 5: Promedio Inicio a Proceso =====
            self._agregar_grafica_inicio_proceso(df, wb)
            
            # ===== GRÁFICA 6: Promedio Proceso a Fin =====
            self._agregar_grafica_proceso_fin(df, wb)
            
            # ===== GRÁFICA 7: Fallas Pendientes (solo las que fueron pendientes) =====
            #self._agregar_grafica_fallas_por_estado(df, wb)
            
            # ===== GRÁFICA 8: Tiempo Pendiente a Fin por Tipo =====
            self._agregar_grafica_tiempo_pendiente_fin(df, wb)

        except Exception as e:
            logger.error(f"Error agregando gráficas: {e}")
            import traceback
            traceback.print_exc()
    
    def _agregar_grafica_fallas_por_tipo(self, df: pd.DataFrame, wb):
        """Gráfica 1: Fallas por Tipo"""
        if 'Tipo' in df.columns:
            df_tipo = df["Tipo"].value_counts()
            if not df_tipo.empty:
                fig, ax = plt.subplots(figsize=(10, 6))
                colores = [self.theme.get_color_para_tipo(t) for t in df_tipo.index]
                df_tipo.plot(kind="bar", ax=ax, title="Fallas por Tipo", color=colores)
                ax.set_xlabel("Tipo")
                ax.set_ylabel("Cantidad")
                ax.tick_params(axis='x', rotation=45)
                self._embed_grafica_en_excel(fig, wb, "Fallas por Tipo")

    def _agregar_grafica_fallas_por_maquina(self, df: pd.DataFrame, wb):
        """Gráfica 2: Fallas por Máquina - MOSTRAR TODAS"""
        if 'Máquina' in df.columns:
            # Mostrar TODAS las máquinas, no solo top 15
            df_maq = df["Máquina"].value_counts()
            if not df_maq.empty:
                fig, ax = plt.subplots(figsize=(max(12, len(df_maq) * 0.3), 8))
                
                # Ordenar para mejor visualización
                df_maq = df_maq.sort_values(ascending=False)
                
                # Crear colores graduales
                cmap = plt.cm.viridis
                colors = [cmap(i/len(df_maq)) for i in range(len(df_maq))]
                
                bars = ax.bar(range(len(df_maq)), df_maq.values, color=colors)
                ax.set_xticks(range(len(df_maq)))
                ax.set_xticklabels(df_maq.index, rotation=45, ha='right', fontsize=9)
                ax.set_title("Fallas por Máquina", fontsize=14, fontweight='bold')
                ax.set_xlabel("Máquina")
                ax.set_ylabel("Cantidad")
                
                # Agregar valores sobre las barras
                for i, (bar, val) in enumerate(zip(bars, df_maq.values)):
                    ax.text(bar.get_x() + bar.get_width()/2, val + 0.5, 
                        str(val), ha='center', va='bottom', fontweight='bold', fontsize=8)
                
                plt.tight_layout()
                self._embed_grafica_en_excel(fig, wb, "Fallas por Máquina")
    
    def _agregar_grafica_fallas_por_tipo_y_maquina(self, df: pd.DataFrame, wb):
        """Gráfica 3: Fallas por Tipo en cada Máquina - MOSTRAR TODAS"""
        if 'Máquina' in df.columns and 'Tipo' in df.columns:
            try:
                # Crear tabla pivote con TODAS las máquinas y tipos
                pivot = pd.pivot_table(df, index='Máquina', columns='Tipo',
                                    aggfunc='size', fill_value=0)
                
                if not pivot.empty:
                    # Calcular tamaño de figura basado en número de máquinas
                    fig_height = max(8, len(pivot) * 0.4)
                    fig_width = max(12, len(pivot.columns) * 0.5)
                    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
                    
                    # Colores para cada tipo
                    colores = [self.theme.get_color_para_tipo(t) for t in pivot.columns]
                    
                    # Crear gráfica de barras apiladas
                    pivot.plot(kind="bar", stacked=True, ax=ax, color=colores)
                    
                    ax.set_title("Fallas por Tipo en cada Máquina", fontsize=14, fontweight='bold')
                    ax.set_xlabel("Máquina")
                    ax.set_ylabel("Cantidad de Fallas")
                    ax.tick_params(axis='x', rotation=45, labelsize=8)
                    ax.legend(title="Tipo", bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
                    
                    # Agregar totales sobre las barras
                    total_por_maquina = pivot.sum(axis=1)
                    for i, (idx, total) in enumerate(total_por_maquina.items()):
                        if total > 0:
                            ax.text(i, total + 0.5, str(total), 
                                ha='center', va='bottom', fontweight='bold', fontsize=8)
                    
                    plt.tight_layout()
                    self._embed_grafica_en_excel(fig, wb, "Fallas por Máq y Tipo")
                    
            except Exception as e:
                logger.error(f"Error en gráfica stacked: {e}")
   
    def _agregar_grafica_tiempo_total_promedio(self, df: pd.DataFrame, wb):
        """Gráfica 4: Tiempo Total Promedio por Tipo"""
        if 'T. Total' in df.columns and 'Tipo' in df.columns:
            try:
                df_temp = df.copy()
                df_temp['T. Total'] = df_temp['T. Total'].astype(str)
                df_temp['T. Total'] = pd.to_timedelta(df_temp['T. Total'].str.extract(r'(\d+:\d+:\d+)')[0])
                df_total = df_temp.groupby("Tipo")["T. Total"].mean().dropna()
                if not df_total.empty:
                    df_total_horas = df_total.dt.total_seconds() / 3600
                    fig, ax = plt.subplots(figsize=(10, 6))
                    colores = [self.theme.get_color_para_tipo(t) for t in df_total_horas.index]
                    df_total_horas.plot(kind="bar", ax=ax,
                                      title="Tiempo Total Promedio por Tipo (horas)",
                                      color=colores)
                    ax.set_xlabel("Tipo")
                    ax.set_ylabel("Horas")
                    ax.tick_params(axis='x', rotation=45)
                    self._embed_grafica_en_excel(fig, wb, "Tiempo Total x Tipo")
            except Exception as e:
                logger.error(f"Error en gráfica tiempo total: {e}")

    def _agregar_grafica_inicio_proceso(self, df: pd.DataFrame, wb):
        """Gráfica 5: Promedio Inicio a Proceso por Tipo"""
        if 'T. Inicio-Proceso' in df.columns and 'Tipo' in df.columns:
            try:
                df_temp = df.copy()
                df_temp['T. Inicio-Proceso'] = df_temp['T. Inicio-Proceso'].astype(str)
                df_temp['T. Inicio-Proceso'] = pd.to_timedelta(df_temp['T. Inicio-Proceso'].str.extract(r'(\d+:\d+:\d+)')[0])
                df_ini_proc = df_temp.groupby("Tipo")["T. Inicio-Proceso"].mean().dropna()
                if not df_ini_proc.empty:
                    df_ini_proc_min = df_ini_proc.dt.total_seconds() / 60
                    fig, ax = plt.subplots(figsize=(10, 6))
                    colores = [self.theme.get_color_para_tipo(t) for t in df_ini_proc_min.index]
                    df_ini_proc_min.plot(kind="bar", ax=ax,
                                      title="Promedio Inicio a Proceso (minutos)",
                                      color=colores)
                    ax.set_xlabel("Tipo")
                    ax.set_ylabel("Minutos")
                    ax.tick_params(axis='x', rotation=45)
                    self._embed_grafica_en_excel(fig, wb, "Inicio-Proceso")
            except Exception as e:
                logger.error(f"Error en gráfica inicio-proceso: {e}")

    def _agregar_grafica_proceso_fin(self, df: pd.DataFrame, wb):
        """Gráfica 6: Promedio Proceso a Fin por Tipo"""
        if 'T. Proceso-Fin' in df.columns and 'Tipo' in df.columns:
            try:
                df_temp = df.copy()
                df_temp['T. Proceso-Fin'] = df_temp['T. Proceso-Fin'].astype(str)
                df_temp['T. Proceso-Fin'] = pd.to_timedelta(df_temp['T. Proceso-Fin'].str.extract(r'(\d+:\d+:\d+)')[0])
                df_proc_fin = df_temp.groupby("Tipo")["T. Proceso-Fin"].mean().dropna()
                if not df_proc_fin.empty:
                    df_proc_fin_min = df_proc_fin.dt.total_seconds() / 60
                    fig, ax = plt.subplots(figsize=(10, 6))
                    colores = [self.theme.get_color_para_tipo(t) for t in df_proc_fin_min.index]
                    df_proc_fin_min.plot(kind="bar", ax=ax,
                                      title="Promedio Proceso a Fin (minutos)",
                                      color=colores)
                    ax.set_xlabel("Tipo")
                    ax.set_ylabel("Minutos")
                    ax.tick_params(axis='x', rotation=45)
                    self._embed_grafica_en_excel(fig, wb, "Proceso-Fin")
            except Exception as e:
                logger.error(f"Error en gráfica proceso-fin: {e}")

    def _agregar_grafica_fallas_por_estado(self, df: pd.DataFrame, wb):
        """Gráfica 7: Fallas que fueron Pendientes (con fecha_pendiente)"""
        # Verificar si hay fallas pendientes en el historial
        if 'fecha_pendiente' in df.columns:
            # Filtrar solo fallas que fueron marcadas como pendientes (tienen fecha_pendiente)
            pendientes_real = df[df['fecha_pendiente'].notna()]
            
            if not pendientes_real.empty:
                # Agrupar por tipo
                pendientes_por_tipo = pendientes_real["Tipo"].value_counts()
                
                if not pendientes_por_tipo.empty:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    colores = [self.theme.get_color_para_tipo(t) for t in pendientes_por_tipo.index]
                    
                    bars = pendientes_por_tipo.plot(kind="bar", ax=ax, 
                                                    title="Fallas Marcadas como Pendientes",
                                                    color=colores)
                    ax.set_xlabel("Tipo de Falla")
                    ax.set_ylabel("Cantidad de Pendientes")
                    ax.tick_params(axis='x', rotation=45)
                    
                    # Agregar valores sobre las barras
                    for i, v in enumerate(pendientes_por_tipo.values):
                        ax.text(i, v + 0.1, str(v), ha='center', va='bottom', fontweight='bold')
                    
                    plt.tight_layout()
                    self._embed_grafica_en_excel(fig, wb, "Fallas Pendientes")
            else:
                # Si no hay fallas pendientes, crear un mensaje
                fig, ax = plt.subplots(figsize=(8, 4))
                ax.text(0.5, 0.5, "No hay fallas marcadas como pendientes en este período",
                    ha='center', va='center', fontsize=12, transform=ax.transAxes)
                ax.set_title("Fallas Pendientes", fontsize=14, fontweight='bold')
                ax.axis('off')
                self._embed_grafica_en_excel(fig, wb, "Fallas Pendientes")
        else:
            # Si no hay columna fecha_pendiente, mostrar mensaje
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.text(0.5, 0.5, "No se encontraron datos de fallas pendientes",
                ha='center', va='center', fontsize=12, transform=ax.transAxes)
            ax.set_title("Fallas Pendientes", fontsize=14, fontweight='bold')
            ax.axis('off')
            self._embed_grafica_en_excel(fig, wb, "Fallas Pendientes")
    
    def _agregar_grafica_pendientes_por_tipo(self, df: pd.DataFrame, wb):
        """Gráfica 8: Fallas Pendientes por Tipo (fallas que fueron marcadas como pendientes)"""
        if 'Tipo' in df.columns and 'Estado' in df.columns:
            pendientes = df[df['Estado'] == 'pendiente']
            if not pendientes.empty:
                pendientes_por_tipo = pendientes["Tipo"].value_counts()
                if not pendientes_por_tipo.empty:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    colores = [self.theme.get_color_para_tipo(t) for t in pendientes_por_tipo.index]
                    pendientes_por_tipo.plot(kind="bar", ax=ax,
                                            title="Fallas Pendientes por Tipo",
                                            color=colores)
                    ax.set_xlabel("Tipo")
                    ax.set_ylabel("Cantidad de Pendientes")
                    ax.tick_params(axis='x', rotation=45)
                    self._embed_grafica_en_excel(fig, wb, "Pendientes por Tipo")

    def _agregar_grafica_tiempo_pendiente_fin(self, df: pd.DataFrame, wb):
        """Gráfica 9: Tiempo Promedio desde que se marcó pendiente hasta resolución"""
        if 'Estado' in df.columns and 'fecha_pendiente' in df.columns and 'fin' in df.columns:
            try:
                # Filtrar fallas que fueron pendientes y tienen fecha_pendiente y fin
                pendientes = df[(df['Estado'] == 'resuelta') & (df['fecha_pendiente'].notna()) & (df['fin'].notna())]
                if not pendientes.empty:
                    # Convertir fechas
                    pendientes['fecha_pendiente_dt'] = pd.to_datetime(pendientes['fecha_pendiente'])
                    pendientes['fin_dt'] = pd.to_datetime(pendientes['fin'])
                    # Calcular tiempo pendiente a fin
                    pendientes['tiempo_pendiente_min'] = (pendientes['fin_dt'] - pendientes['fecha_pendiente_dt']).dt.total_seconds() / 60
                    
                    # Agrupar por tipo
                    tiempo_por_tipo = pendientes.groupby("Tipo")["tiempo_pendiente_min"].mean().dropna()
                    if not tiempo_por_tipo.empty:
                        fig, ax = plt.subplots(figsize=(10, 6))
                        colores = [self.theme.get_color_para_tipo(t) for t in tiempo_por_tipo.index]
                        tiempo_por_tipo.plot(kind="bar", ax=ax,
                                            title="Tiempo Promedio Pendiente a Resolución (minutos)",
                                            color=colores)
                        ax.set_xlabel("Tipo")
                        ax.set_ylabel("Minutos Promedio")
                        ax.tick_params(axis='x', rotation=45)
                        self._embed_grafica_en_excel(fig, wb, "Tiempo Pendiente a Fin")
            except Exception as e:
                logger.error(f"Error en gráfica tiempo pendiente-fin: {e}")

    def _embed_grafica_en_excel(self, fig, wb, titulo):
        """Inserta una figura en el workbook de Excel"""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
        plt.close(fig)
        buf.seek(0)
        
        # Limpiar nombre de hoja (Excel tiene límite de 31 caracteres)
        sheet_name = titulo[:31]
        ws = wb.create_sheet(title=sheet_name)
        img = ExcelImage(buf)
        img.anchor = 'A1'
        ws.add_image(img)

    def exportar_excel_simple(self, datos: List[Dict], file_path: str) -> bool:
        """Exporta datos sin gráficas"""
        try:
            if isinstance(datos[0], dict):
                df = pd.DataFrame(datos)
                columnas_interes = ['id', 'maquina', 'tipo', 'inicio', 'proceso',
                                   'fin', 't_inicio_proceso', 't_proceso_fin', 
                                   't_total', 'numero_falla']
                columnas_existentes = [col for col in columnas_interes if col in df.columns]
                df = df[columnas_existentes]
                
                nombre_map = {
                    'id': 'ID', 'maquina': 'Máquina', 'tipo': 'Tipo',
                    'inicio': 'Inicio', 'proceso': 'Proceso', 'fin': 'Fin',
                    't_inicio_proceso': 'T. Inicio-Proceso',
                    't_proceso_fin': 'T. Proceso-Fin',
                    't_total': 'T. Total', 'numero_falla': '# Falla'
                }
                df.rename(columns={k: v for k, v in nombre_map.items() if k in df.columns}, 
                         inplace=True)
            
            df.to_excel(file_path, index=False)
            logger.info(f" Excel simple exportado a {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exportando Excel simple: {e}")
            return False