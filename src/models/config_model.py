# src/models/config_model.py

import json
import logging
from typing import Optional, Dict, Any
from src.models.database import Database
from src.utils.constants import DB_CONFIG_FILE, DB_CONFIG_DEFAULT

logger = logging.getLogger(__name__)

class ConfigModel:
    """Modelo para manejar configuraciones del sistema"""
    
    def __init__(self, db: Database):
        self.db = db

    # ===== CONFIGURACIÓN DE BD (archivo JSON) =====
    
    @staticmethod
    def cargar_config_db() -> dict:
        """Carga la configuración de la base de datos desde JSON"""
        config = DB_CONFIG_DEFAULT.copy()
        try:
            with open(DB_CONFIG_FILE, 'r') as f:
                loaded = json.load(f)
                config.update(loaded)
        except FileNotFoundError:
            logger.info("Archivo de configuración no encontrado, usando valores por defecto")
        except Exception as e:
            logger.error(f"Error cargando config: {e}")
        return config

    @staticmethod
    def guardar_config_db(config: dict) -> bool:
        """Guarda la configuración de la base de datos en JSON"""
        try:
            with open(DB_CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
            logger.info("✅ Configuración de BD guardada")
            return True
        except Exception as e:
            logger.error(f"❌ Error guardando config: {e}")
            return False

    # ===== CONFIGURACIÓN DEL SISTEMA (MySQL) =====
    
    def cargar_config_sistema(self) -> dict:
        """Carga la configuración del sistema desde MySQL"""
        config = {
            "nombre_sistema": "ANDON SYSTEM",
            "tema_activo": "oscuro",
            "color_fondo": "#1a1a2e",
            "color_sidebar": "#16213e",
            "color_card": "#0f3460",
            "superficie3": "#2d3047",
            "color_texto": "#ffffff",
            "texto_principal": "#ffffff",
            "color_texto_secundario": "#b0b0b0",
            "texto_secundario": "#b0b0b0",
            "color_acento": "#e94560",
            "acento_principal": "#e94560",
            "color_exito": "#00C853",
            "exito": "#00C853",
            "color_warning": "#FFC107",
            "advertencia": "#FFC107",
            "color_danger": "#FF5252",
            "peligro": "#FF5252",
            "color_pendiente": "#FFA500",
            "pendiente": "#FFA500"
        }
        
        conn = self.db.get_connection()
        if not conn:
            logger.warning("No se pudo conectar a MySQL, usando valores por defecto")
            return config
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM config_sistema WHERE id = 1")
            row = cursor.fetchone()
            if row:
                for key in config.keys():
                    if key in row and row[key] is not None:
                        config[key] = row[key]
            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"Error cargando config_sistema: {e}")
            if conn:
                conn.close()
        
        return config

    def guardar_config_sistema(self, config: dict) -> bool:
        """Guarda la configuración del sistema en MySQL"""
        conn = self.db.get_connection()
        if not conn:
            logger.error("No se pudo conectar a MySQL")
            return False
        
        try:
            cursor = conn.cursor()
            
            # Verificar columnas
            cursor.execute("SHOW COLUMNS FROM config_sistema")
            columnas_existentes = [col[0] for col in cursor.fetchall()]
            
            # Verificar si existe registro
            cursor.execute("SELECT id FROM config_sistema WHERE id = 1")
            existe = cursor.fetchone()
            
            campos = []
            valores = []
            
            # Mapeo de campos (igual que en tu código original)
            campos.append("nombre_sistema = %s")
            valores.append(config.get("nombre_sistema", "ANDON SYSTEM"))
            
            if "tema_activo" in columnas_existentes:
                campos.append("tema_activo = %s")
                valores.append(config.get("tema_activo", "oscuro"))
            
            # ... (incluir todos los demás campos como en tu original)
            
            if existe:
                query = f"UPDATE config_sistema SET {', '.join(campos)} WHERE id = 1"
                cursor.execute(query, valores)
            else:
                campos_insert = ["id"] + [c.split(" = ")[0] for c in campos]
                placeholders = ["%s"] * len(campos_insert)
                valores_insert = [1] + valores
                query = f"INSERT INTO config_sistema ({', '.join(campos_insert)}) VALUES ({', '.join(placeholders)})"
                cursor.execute(query, valores_insert)
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info("✅ Configuración del sistema guardada")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando config_sistema: {e}")
            if conn:
                conn.rollback()
                conn.close()
            return False

    # ===== CONFIGURACIÓN DE PROYECCIÓN =====
    
    def cargar_config_proyeccion(self) -> dict:
        """Carga la configuración de proyección desde MySQL"""
        from src.utils.constants import PROYECCION_DEFAULT
        config = PROYECCION_DEFAULT.copy()
        
        conn = self.db.get_connection()
        if not conn:
            return config
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM config_proyeccion WHERE id = 1")
            row = cursor.fetchone()
            if row:
                for key in config.keys():
                    if key in row and row[key] is not None:
                        config[key] = row[key]
            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"Error cargando config_proyeccion: {e}")
            if conn:
                conn.close()
        
        return config

    def guardar_config_proyeccion(self, config: dict) -> bool:
        """Guarda la configuración de proyección en MySQL"""
        conn = self.db.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE config_proyeccion SET
                    pantalla_completa = %s,
                    recordar_posicion = %s,
                    x = %s,
                    y = %s,
                    ancho = %s,
                    alto = %s,
                    monitor = %s,
                    color_fondo = %s,
                    mostrar_contador = %s,
                    color_texto = %s,
                    color_acento = %s,
                    color_exito = %s,
                    mostrar_pendientes = %s
                WHERE id = 1
            ''', (
                config["pantalla_completa"],
                config["recordar_posicion"],
                config["x"],
                config["y"],
                config["ancho"],
                config["alto"],
                config["monitor"],
                config["color_fondo"],
                config["mostrar_contador"],
                config["color_texto"],
                config["color_acento"],
                config["color_exito"],
                config.get("mostrar_pendientes", True)
            ))
            conn.commit()
            cursor.close()
            conn.close()
            logger.info("✅ Configuración de proyección guardada")
            return True
        except Exception as e:
            logger.error(f"Error guardando config_proyeccion: {e}")
            if conn:
                conn.rollback()
                conn.close()
            return False

    # ===== CONFIGURACIÓN DE CONTADOR =====
    
    def cargar_config_contador(self) -> dict:
        """Carga la configuración del contador desde MySQL"""
        from src.utils.constants import CONTADOR_DEFAULT
        config = CONTADOR_DEFAULT.copy()
        
        conn = self.db.get_connection()
        if not conn:
            return config
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM config_contador WHERE id = 1")
            row = cursor.fetchone()
            if row:
                config["ultimo_reset"] = row["ultimo_reset"].strftime("%Y-%m-%d %H:%M:%S") if row["ultimo_reset"] else config["ultimo_reset"]
                config["consecutivo_actual"] = row["consecutivo_actual"] or 0
                config["periodo_reset"] = row["periodo_reset"] or "diario"
            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"Error cargando config_contador: {e}")
            if conn:
                conn.close()
        
        return config

    def guardar_config_contador(self, config: dict) -> bool:
        """Guarda la configuración del contador en MySQL"""
        conn = self.db.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE config_contador SET
                    ultimo_reset = %s,
                    consecutivo_actual = %s,
                    periodo_reset = %s
                WHERE id = 1
            ''', (
                config["ultimo_reset"],
                config["consecutivo_actual"],
                config["periodo_reset"]
            ))
            conn.commit()
            cursor.close()
            conn.close()
            logger.info("✅ Configuración de contador guardada")
            return True
        except Exception as e:
            logger.error(f"Error guardando config_contador: {e}")
            if conn:
                conn.rollback()
                conn.close()
            return False