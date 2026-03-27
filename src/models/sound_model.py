# src/models/sound_model.py

import logging
from typing import Dict, Optional
from src.models.database import Database

logger = logging.getLogger(__name__)

class SoundModel:
    """Modelo para manejar la configuración de sonidos por tipo de falla"""

    def __init__(self, db: Database):
        self.db = db

    def guardar_sonido(self, tipo_falla: str, ruta_archivo: str) -> bool:
        """Guarda o actualiza la ruta del sonido para un tipo de falla"""
        conn = self.db.get_connection()
        if not conn:
            logger.error("No se pudo conectar a MySQL")
            return False

        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sonidos_falla (tipo_falla, ruta_archivo)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE
                ruta_archivo = VALUES(ruta_archivo)
            ''', (tipo_falla, ruta_archivo))
            conn.commit()
            cursor.close()
            conn.close()
            logger.info(f"Sonido guardado para tipo '{tipo_falla}'")
            return True
        except Exception as e:
            logger.error(f"Error guardando sonido: {e}")
            if conn:
                conn.rollback()
                conn.close()
            return False

    def cargar_sonidos(self) -> Dict[str, str]:
        """Carga todos los sonidos configurados, devuelve dict {tipo_falla: ruta_archivo}"""
        sonidos = {}
        conn = self.db.get_connection()
        if not conn:
            return sonidos

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT tipo_falla, ruta_archivo FROM sonidos_falla")
            for tipo, ruta in cursor.fetchall():
                sonidos[tipo] = ruta
            cursor.close()
            conn.close()
            logger.info(f"Cargados {len(sonidos)} sonidos configurados")
        except Exception as e:
            logger.error(f"Error cargando sonidos: {e}")
            if conn:
                conn.close()

        return sonidos

    def eliminar_sonido(self, tipo_falla: str) -> bool:
        """Elimina la configuración de sonido para un tipo de falla"""
        conn = self.db.get_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sonidos_falla WHERE tipo_falla = %s", (tipo_falla,))
            conn.commit()
            afectadas = cursor.rowcount
            cursor.close()
            conn.close()
            if afectadas > 0:
                logger.info(f"Sonido eliminado para tipo '{tipo_falla}'")
            return True
        except Exception as e:
            logger.error(f"Error eliminando sonido: {e}")
            if conn:
                conn.rollback()
                conn.close()
            return False