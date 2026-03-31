# src/models/database.py

import mysql.connector
from mysql.connector import pooling
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class Database:
    """Singleton para gestionar el pool de conexiones a MySQL"""
    
    _instance = None
    _pool = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(self, config: dict) -> bool:
        """Inicializa el pool de conexiones con la configuración dada"""
        self._config = config
        try:
            self._pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name="andon_pool",
                pool_size=5,
                host=config["host"],
                port=config["port"],
                user=config["usuario"],
                password=config["password"],
                database=config["base_datos"],
                connection_timeout=config.get("timeout", 30),
                ssl_disabled=not config.get("usar_ssl", False),
                use_pure=True,
                autocommit=False,
                buffered=True,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
            logger.info("Pool de conexiones MySQL creado")
            return True
        except Exception as e:
            logger.error(f"Error creando pool: {e}")
            self._pool = None
            return False

    def get_connection(self) -> Optional[mysql.connector.MySQLConnection]:
        """Obtiene una conexión del pool"""
        if self._pool:
            try:
                return self._pool.get_connection()
            except Exception as e:
                logger.error(f"Error obteniendo conexión: {e}")
        return None

    def test_connection(self) -> tuple[bool, str]:
        """Prueba la conexión a MySQL con mejor manejo de errores"""
        try:
            # Importar aquí para evitar problemas de importación
            import mysql.connector
            from mysql.connector import Error as MySQLError
            
            # Intentar conectar
            conn = mysql.connector.connect(
                host=self._config["host"],
                port=self._config["port"],
                user=self._config["usuario"],
                password=self._config["password"],
                database=self._config["base_datos"],
                connection_timeout=self._config.get("timeout", 30),
                ssl_disabled=not self._config.get("usar_ssl", False),
                use_pure=True  # Forzar implementación pura
            )
            conn.close()
            return True, "Conexión exitosa"
            
        except ImportError as e:
            return False, f"No se pudo importar mysql.connector: {str(e)}"
            
        except mysql.connector.Error as e:
            error_code = e.errno if hasattr(e, 'errno') else 0
            error_msg = str(e)
            
            # Mensajes de error más descriptivos
            if error_code == 1045:
                return False, f"Error de autenticación (1045): Usuario o contraseña incorrectos"
            elif error_code == 1049:
                return False, f"Base de datos no existe (1049): {self._config['base_datos']}"
            elif error_code == 2003:
                return False, f"No se pudo conectar al servidor (2003): {self._config['host']}:{self._config['port']}"
            elif error_code == 2005:
                return False, f"Host desconocido (2005): {self._config['host']}"
            else:
                return False, f"Error MySQL ({error_code}): {error_msg}"
                
        except Exception as e:
            return False, f"Error inesperado: {str(e)}"

    @property
    def is_connected(self) -> bool:
        """Verifica si hay pool y conexiones disponibles"""
        if not self._pool:
            return False
        try:
            conn = self.get_connection()
            if conn:
                conn.close()
                return True
        except:
            pass
        return False