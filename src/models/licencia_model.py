# src/models/licencia_model.py

import mysql.connector
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
from src.models.database import Database
from src.utils.constants import LICENSE_DB_CONFIG, LICENSE_DEFAULTS

logger = logging.getLogger(__name__)

class LicenciaModel:
    """Modelo para manejar licencias"""
    
    def __init__(self, db: Database):
        self.db = db

    # ===== CONFIGURACIÓN LOCAL DE LICENCIA =====
    
    def cargar_config_licencia(self) -> dict:
        """Carga la configuración de licencia desde MySQL local"""
        config = LICENSE_DEFAULTS.copy()
        
        conn = self.db.get_connection()
        if not conn:
            logger.warning("No se pudo conectar a MySQL local, usando valores por defecto")
            return config
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM config_licencia WHERE id = 1")
            row = cursor.fetchone()
            if row:
                for key in config.keys():
                    if key in row and row[key] is not None:
                        if isinstance(row[key], datetime):
                            config[key] = row[key].strftime("%Y-%m-%d %H:%M:%S")
                        elif hasattr(row[key], 'strftime'):
                            config[key] = row[key].strftime("%Y-%m-%d")
                        else:
                            config[key] = row[key]
            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"Error cargando config_licencia: {e}")
            if conn:
                conn.close()
        
        return config

    def guardar_config_licencia(self, config: dict) -> bool:
        """Guarda la configuración de licencia en MySQL local"""
        conn = self.db.get_connection()
        if not conn:
            logger.error("No se pudo conectar a MySQL local")
            return False
        
        try:
            cursor = conn.cursor()
            
            def mysql_null_if_empty(val):
                return None if val == "" else val
            
            cursor.execute('''
                INSERT INTO config_licencia (
                    id, installation_id, license_key, license_type, demo_used,
                    demo_start, demo_expires, max_fallas, max_maquinas,
                    last_validation, grace_period_start, excel_exports_today, 
                    last_export_date, expires_at
                ) VALUES (1, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    installation_id = VALUES(installation_id),
                    license_key = VALUES(license_key),
                    license_type = VALUES(license_type),
                    demo_used = VALUES(demo_used),
                    demo_start = VALUES(demo_start),
                    demo_expires = VALUES(demo_expires),
                    max_fallas = VALUES(max_fallas),
                    max_maquinas = VALUES(max_maquinas),
                    last_validation = VALUES(last_validation),
                    grace_period_start = VALUES(grace_period_start),
                    excel_exports_today = VALUES(excel_exports_today),
                    last_export_date = VALUES(last_export_date),
                    expires_at = VALUES(expires_at)
            ''', (
                config.get("installation_id", ""),
                config.get("license_key", ""),
                config.get("license_type", "basic"),
                config.get("demo_used", False),
                mysql_null_if_empty(config.get("demo_start", "")),
                mysql_null_if_empty(config.get("demo_expires", "")),
                config.get("max_fallas", 3),
                config.get("max_maquinas", 5),
                mysql_null_if_empty(config.get("last_validation", "")),
                mysql_null_if_empty(config.get("grace_period_start", "")),
                config.get("excel_exports_today", 0),
                mysql_null_if_empty(config.get("last_export_date", "")),
                mysql_null_if_empty(config.get("expires_at", ""))
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info(f"✅ Licencia guardada: {config.get('license_type')}")
            return True
        except Exception as e:
            logger.error(f"Error guardando licencia: {e}")
            if conn:
                conn.rollback()
                conn.close()
            return False

    # ===== VALIDACIÓN ONLINE =====
    
    def validar_licencia_online(self, license_key: str, installation_id: str) -> Tuple[bool, any]:
        """Valida la licencia contra el servidor central"""
        logger.info(f"🔍 Validando licencia: {license_key}")
        
        try:
            # Intentar con SSL primero
            try:
                conn = mysql.connector.connect(
                    host=LICENSE_DB_CONFIG["host"],
                    port=LICENSE_DB_CONFIG["port"],
                    user=LICENSE_DB_CONFIG["usuario"],
                    password=LICENSE_DB_CONFIG["password"],
                    database=LICENSE_DB_CONFIG["base_datos"],
                    connection_timeout=LICENSE_DB_CONFIG["timeout"],
                    ssl_disabled=False,
                    use_pure=True
                )
            except:
                conn = mysql.connector.connect(
                    host=LICENSE_DB_CONFIG["host"],
                    port=LICENSE_DB_CONFIG["port"],
                    user=LICENSE_DB_CONFIG["usuario"],
                    password=LICENSE_DB_CONFIG["password"],
                    database=LICENSE_DB_CONFIG["base_datos"],
                    connection_timeout=LICENSE_DB_CONFIG["timeout"],
                    ssl_disabled=True,
                    use_pure=True
                )
            
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT * FROM licencias
                WHERE license_key = %s AND is_active = 1
            """, (license_key,))
            
            licencia = cursor.fetchone()
            
            if not licencia:
                conn.close()
                return False, "Licencia no válida o inactiva"
            
            # Verificar asignación
            if licencia['installation_id'] and licencia['installation_id'] != installation_id:
                conn.close()
                return False, "Licencia ya asignada a otra instalación"
            
            # Verificar expiración
            hoy = datetime.now().date()
            expiracion = licencia['expires_at']
            if isinstance(expiracion, str):
                expiracion = datetime.strptime(expiracion, "%Y-%m-%d").date()
            
            if hoy > expiracion:
                conn.close()
                return False, f"Licencia expirada el {expiracion}"
            
            # Actualizar la licencia
            cursor.execute("""
                UPDATE licencias SET 
                    installation_id = %s,
                    last_validated = NOW()
                WHERE id = %s
            """, (installation_id, licencia['id']))
            
            conn.commit()
            conn.close()
            
            return True, {
                'license_type': licencia['license_type'],
                'max_fallas': licencia['max_fallas'],
                'max_maquinas': licencia['max_maquinas'],
                'expires_at': expiracion.strftime("%Y-%m-%d")
            }
            
        except mysql.connector.Error as e:
            error_msg = str(e)
            logger.error(f"Error MySQL validando licencia: {error_msg}")
            if "2003" in error_msg:
                return False, "No se pudo conectar al servidor de licencias"
            elif "1045" in error_msg:
                return False, "Error de autenticación"
            else:
                return False, f"Error de conexión: {error_msg}"
        except Exception as e:
            logger.error(f"Error general validando licencia: {e}")
            return False, f"Error inesperado: {str(e)}"

    def iniciar_demo(self, installation_id: str) -> Tuple[bool, str]:
        """Inicia un periodo de demo"""
        logger.info(f"🎁 Iniciando demo para: {installation_id}")
        
        try:
            # Obtener IP
            ip_address = "0.0.0.0"
            try:
                import socket
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ip_address = s.getsockname()[0]
                s.close()
            except:
                pass

            # Conectar al servidor de licencias
            try:
                conn = mysql.connector.connect(
                    host=LICENSE_DB_CONFIG["host"],
                    port=LICENSE_DB_CONFIG["port"],
                    user=LICENSE_DB_CONFIG["usuario"],
                    password=LICENSE_DB_CONFIG["password"],
                    database=LICENSE_DB_CONFIG["base_datos"],
                    connection_timeout=LICENSE_DB_CONFIG["timeout"],
                    ssl_disabled=False,
                    use_pure=True
                )
            except:
                conn = mysql.connector.connect(
                    host=LICENSE_DB_CONFIG["host"],
                    port=LICENSE_DB_CONFIG["port"],
                    user=LICENSE_DB_CONFIG["usuario"],
                    password=LICENSE_DB_CONFIG["password"],
                    database=LICENSE_DB_CONFIG["base_datos"],
                    connection_timeout=LICENSE_DB_CONFIG["timeout"],
                    ssl_disabled=True,
                    use_pure=True
                )

            cursor = conn.cursor(dictionary=True)

            # Verificar si ya existe
            cursor.execute("""
                SELECT * FROM demo_installations 
                WHERE installation_id = %s
            """, (installation_id,))
            
            if cursor.fetchone():
                conn.close()
                return False, "Ya has utilizado el periodo de demo"

            # Crear demo
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            fecha_expiracion = (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d")

            cursor.execute("""
                INSERT INTO demo_installations 
                (installation_id, ip_address, started_at, expires_at, is_expired, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                installation_id, 
                ip_address, 
                fecha_actual, 
                fecha_expiracion,
                0,
                fecha_actual
            ))

            conn.commit()
            conn.close()

            logger.info(f"✅ Demo iniciado, expira: {fecha_expiracion}")
            return True, fecha_expiracion

        except Exception as e:
            logger.error(f"Error iniciando demo: {e}")
            return False, f"Error: {str(e)}"

    # ===== VERIFICACIÓN DE ESTADO =====
    
    def verificar_estado_licencia(self, config: dict) -> Tuple[bool, any]:
        """Verifica el estado de la licencia"""
        logger.info("🔍 Verificando estado de licencia...")
        
        hoy = datetime.now()

        # Licencia de pago
        if config.get('license_key') and config.get('license_type') in ['pro', 'mid']:
            if config.get('expires_at'):
                try:
                    expiracion = datetime.strptime(config['expires_at'], "%Y-%m-%d")
                    if hoy.date() > expiracion.date():
                        logger.warning("❌ Licencia expirada")
                        return False, "Licencia expirada"
                except:
                    pass
            logger.info(f"✅ Licencia {config['license_type'].upper()} válida")
            return True, config

        # Demo
        elif config.get('demo_used') and config.get('demo_expires'):
            try:
                demo_expira = datetime.strptime(config['demo_expires'], "%Y-%m-%d")
                if hoy.date() <= demo_expira.date():
                    logger.info("✅ Demo activa")
                    return True, config
                else:
                    logger.warning("❌ Demo expirada")
                    return False, "Periodo de demo expirado"
            except:
                return False, "Error en fecha de demo"

        # Básico por defecto
        else:
            logger.info("ℹ️ Modo básico activado")
            return True, config