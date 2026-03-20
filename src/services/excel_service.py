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
                self._agregar_graficas(df, wb)
                wb.save(file_path)

            logger.info(f"Excel exportado a {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error exportando Excel: {e}")
            return False

    def _agregar_graficas(self, df: pd.DataFrame, wb):
        """Agrega todas las gráficas al archivo Excel"""
        try:
            # Gráfica 1: Fallas por Tipo
            if 'Tipo' in df.columns:
                df_tipo = df["Tipo"].value_counts()
                if not df_tipo.empty:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    colores = [self.theme.get_color_para_tipo(t) for t in df_tipo.index]
                    df_tipo.plot(kind="bar", ax=ax, title="Fallas por Tipo", color=colores)
                    ax.set_xlabel("Tipo")
                    ax.set_ylabel("Cantidad")
                    ax.tick_params(axis='x', rotation=45)
                    
                    buf = io.BytesIO()
                    fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
                    plt.close(fig)
                    buf.seek(0)
                    
                    ws = wb.create_sheet(title="Fallas por Tipo")
                    img = ExcelImage(buf)
                    img.anchor = 'A1'
                    ws.add_image(img)

            # Gráfica 2: Fallas por Máquina
            if 'Máquina' in df.columns:
                df_maq = df["Máquina"].value_counts()
                if not df_maq.empty:
                    fig, ax = plt.subplots(figsize=(12, 6))
                    df_maq.plot(kind="bar", ax=ax, title="Fallas por Máquina",
                              color=self.theme.colores.get("accento", "#e94560"))
                    ax.set_xlabel("Máquina")
                    ax.set_ylabel("Cantidad")
                    ax.tick_params(axis='x', rotation=45)
                    
                    buf = io.BytesIO()
                    fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
                    plt.close(fig)
                    buf.seek(0)
                    
                    ws = wb.create_sheet(title="Fallas por Máquina")
                    img = ExcelImage(buf)
                    img.anchor = 'A1'
                    ws.add_image(img)

            # Gráfica 3: Tiempo Total Promedio por Tipo
            if 'T. Total' in df.columns and 'Tipo' in df.columns:
                try:
                    df['T. Total'] = pd.to_timedelta(df['T. Total'].astype(str).str.extract(r'(\d+:\d+:\d+)')[0])
                    df_total = df.groupby("Tipo")["T. Total"].mean().dropna()
                    
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
                        
                        buf = io.BytesIO()
                        fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
                        plt.close(fig)
                        buf.seek(0)
                        
                        ws = wb.create_sheet(title="Tiempo x Tipo")
                        img = ExcelImage(buf)
                        img.anchor = 'A1'
                        ws.add_image(img)
                except Exception as e:
                    logger.error(f"Error en gráfica de tiempos: {e}")

        except Exception as e:
            logger.error(f"Error agregando gráficas: {e}")

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
            logger.info(f"Excel simple exportado a {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exportando Excel simple: {e}")
            return False