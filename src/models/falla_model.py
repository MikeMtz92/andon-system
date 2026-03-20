# src/models/falla_model.py

import logging
from datetime import datetime
from typing import List, Dict, Optional
from src.models.database import Database

logger = logging.getLogger(__name__)

class FallaModel:
    """Modelo para manejar operaciones con fallas"""
    
    def __init__(self, db: Database):
        self.db = db

    # ===== FALLAS ACTIVAS =====
    
    def cargar_fallas_activas(self) -> List[Dict]:
        """Carga las fallas activas desde MySQL"""
        fallas = []
        conn = self.db.get_connection()
        if not conn:
            logger.warning("No se pudo conectar a MySQL para cargar fallas activas")
            return []
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT maquina, tipo, inicio, proceso, fin, numero_falla, 
                       estado, nota_pendiente, fecha_pendiente 
                FROM fallas_activas
            """)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            
            for row in rows:
                falla = {
                    "maquina": row['maquina'],
                    "tipo": row['tipo'],
                    "inicio": row['inicio'].strftime("%Y-%m-%d %H:%M:%S") if row['inicio'] else None,
                    "proceso": row['proceso'].strftime("%Y-%m-%d %H:%M:%S") if row['proceso'] else None,
                    "fin": row['fin'].strftime("%Y-%m-%d %H:%M:%S") if row['fin'] else None,
                    "numero_falla": row['numero_falla'],
                    "estado": row['estado'] or "activa",
                    "nota_pendiente": row['nota_pendiente'],
                    "fecha_pendiente": row['fecha_pendiente'].strftime("%Y-%m-%d %H:%M:%S") if row['fecha_pendiente'] else None
                }
                fallas.append(falla)
            
            logger.info(f"Cargadas {len(fallas)} fallas activas")
        except Exception as e:
            logger.error(f"Error cargando fallas activas: {e}")
            if conn:
                conn.close()
        
        return fallas

    def guardar_fallas_activas(self, fallas_en_memoria: List[Dict]) -> bool:
        """Sincroniza la tabla fallas_activas con la lista en memoria"""
        conn = self.db.get_connection()
        if not conn:
            logger.error("No se pudo conectar a MySQL")
            return False
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Obtener fallas actuales en BD
            cursor.execute("SELECT numero_falla FROM fallas_activas")
            numeros_en_bd = set(row['numero_falla'] for row in cursor.fetchall())
            
            # Números en memoria
            numeros_en_memoria = set(f.get('numero_falla') for f in fallas_en_memoria if f.get('numero_falla'))
            
            # Eliminar las que ya no están
            numeros_a_eliminar = numeros_en_bd - numeros_en_memoria
            if numeros_a_eliminar:
                placeholders = ','.join(['%s'] * len(numeros_a_eliminar))
                cursor.execute(f"DELETE FROM fallas_activas WHERE numero_falla IN ({placeholders})", 
                             tuple(numeros_a_eliminar))
                logger.info(f"Eliminadas {cursor.rowcount} fallas activas")
            
            # Insertar o actualizar
            for falla in fallas_en_memoria:
                numero = falla.get('numero_falla')
                if not numero:
                    continue
                
                if numero in numeros_en_bd:
                    # Actualizar
                    cursor.execute("""
                        UPDATE fallas_activas SET
                            maquina = %s,
                            tipo = %s,
                            inicio = %s,
                            proceso = %s,
                            fin = %s,
                            estado = %s,
                            nota_pendiente = %s,
                            fecha_pendiente = %s
                        WHERE numero_falla = %s
                    """, (
                        falla.get("maquina"),
                        falla.get("tipo"),
                        falla.get("inicio"),
                        falla.get("proceso"),
                        falla.get("fin"),
                        falla.get("estado", "activa"),
                        falla.get("nota_pendiente"),
                        falla.get("fecha_pendiente"),
                        numero
                    ))
                else:
                    # Insertar
                    cursor.execute("""
                        INSERT INTO fallas_activas
                        (maquina, tipo, inicio, proceso, fin, numero_falla, estado, nota_pendiente, fecha_pendiente)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        falla.get("maquina"),
                        falla.get("tipo"),
                        falla.get("inicio"),
                        falla.get("proceso"),
                        falla.get("fin"),
                        numero,
                        falla.get("estado", "activa"),
                        falla.get("nota_pendiente"),
                        falla.get("fecha_pendiente")
                    ))
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info(f"Sincronización completada. {len(fallas_en_memoria)} fallas en memoria")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando fallas activas: {e}")
            if conn:
                conn.rollback()
                conn.close()
            return False

    def guardar_falla_activa(self, alerta: Dict) -> bool:
        """Guarda o actualiza una falla en activas"""
        conn = self.db.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Verificar si existe
            cursor.execute("SELECT id FROM fallas_activas WHERE numero_falla = %s", 
                         (alerta.get("numero_falla"),))
            existe = cursor.fetchone()
            
            if existe:
                cursor.execute("""
                    UPDATE fallas_activas SET
                        maquina = %s,
                        tipo = %s,
                        inicio = %s,
                        proceso = %s,
                        fin = %s,
                        estado = %s,
                        nota_pendiente = %s,
                        fecha_pendiente = %s
                    WHERE numero_falla = %s
                """, (
                    alerta.get("maquina"),
                    alerta.get("tipo"),
                    alerta.get("inicio"),
                    alerta.get("proceso"),
                    alerta.get("fin"),
                    alerta.get("estado", "activa"),
                    alerta.get("nota_pendiente"),
                    alerta.get("fecha_pendiente"),
                    alerta.get("numero_falla")
                ))
            else:
                cursor.execute("""
                    INSERT INTO fallas_activas
                    (maquina, tipo, inicio, proceso, fin, numero_falla, estado, nota_pendiente, fecha_pendiente)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    alerta.get("maquina"),
                    alerta.get("tipo"),
                    alerta.get("inicio"),
                    alerta.get("proceso"),
                    alerta.get("fin"),
                    alerta.get("numero_falla"),
                    alerta.get("estado", "activa"),
                    alerta.get("nota_pendiente"),
                    alerta.get("fecha_pendiente")
                ))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error guardando falla activa: {e}")
            if conn:
                conn.rollback()
                conn.close()
            return False

    def eliminar_falla_activa(self, numero_falla: int) -> bool:
        """Elimina una falla de activas"""
        conn = self.db.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM fallas_activas WHERE numero_falla = %s", (numero_falla,))
            conn.commit()
            cursor.close()
            conn.close()
            logger.info(f"Falla activa #{numero_falla} eliminada")
            return True
        except Exception as e:
            logger.error(f"Error eliminando falla activa: {e}")
            if conn:
                conn.rollback()
                conn.close()
            return False

    # ===== HISTORIAL DE FALLAS =====
    
    def guardar_falla_en_historial(self, alerta: Dict) -> bool:
        """Guarda una falla finalizada en el historial"""
        conn = self.db.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Calcular tiempos (igual que en tu original)
            formato = "%Y-%m-%d %H:%M:%S"
            t_inicio_proceso = None
            t_proceso_fin = None
            t_total = None
            
            inicio = alerta.get("inicio")
            proceso = alerta.get("proceso")
            fin = alerta.get("fin")
            
            if inicio and proceso and fin:
                try:
                    dt_inicio = datetime.strptime(inicio, formato)
                    dt_proceso = datetime.strptime(proceso, formato)
                    dt_fin = datetime.strptime(fin, formato)
                    
                    diff_inicio_proceso = dt_proceso - dt_inicio
                    horas = diff_inicio_proceso.seconds // 3600
                    minutos = (diff_inicio_proceso.seconds % 3600) // 60
                    segundos = diff_inicio_proceso.seconds % 60
                    t_inicio_proceso = f"{horas:02d}:{minutos:02d}:{segundos:02d}"
                    
                    diff_proceso_fin = dt_fin - dt_proceso
                    horas = diff_proceso_fin.seconds // 3600
                    minutos = (diff_proceso_fin.seconds % 3600) // 60
                    segundos = diff_proceso_fin.seconds % 60
                    t_proceso_fin = f"{horas:02d}:{minutos:02d}:{segundos:02d}"
                    
                    diff_total = dt_fin - dt_inicio
                    horas = diff_total.seconds // 3600
                    minutos = (diff_total.seconds % 3600) // 60
                    segundos = diff_total.seconds % 60
                    t_total = f"{horas:02d}:{minutos:02d}:{segundos:02d}"
                except:
                    pass
            
            cursor.execute("""
                INSERT INTO fallas 
                (maquina, tipo, inicio, proceso, fin, numero_falla, 
                 t_inicio_proceso, t_proceso_fin, t_total, estado, 
                 nota_pendiente, fecha_pendiente)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                alerta["maquina"],
                alerta["tipo"],
                inicio,
                proceso,
                fin,
                alerta.get("numero_falla", 0),
                t_inicio_proceso,
                t_proceso_fin,
                t_total,
                "resuelta",
                alerta.get("nota_pendiente"),
                alerta.get("fecha_pendiente")
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info(f"Falla #{alerta.get('numero_falla')} guardada en historial")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando en historial: {e}")
            if conn:
                conn.rollback()
                conn.close()
            return False

    # ===== TIPOS DE FALLA =====
    
    def cargar_tipos_falla(self) -> List[Dict]:
        """Carga los tipos de falla desde MySQL"""
        tipos = []
        conn = self.db.get_connection()
        if not conn:
            logger.warning("Usando tipos por defecto")
            from src.utils.constants import FALLAS_DEFAULT, COLORES_DEFAULT
            return [
                {"nombre": FALLAS_DEFAULT[i], "color": list(COLORES_DEFAULT.values())[i+3]} 
                for i in range(min(5, len(FALLAS_DEFAULT)))
            ]
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT nombre, color FROM tipos_falla ORDER BY orden")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            
            for row in rows:
                tipos.append({"nombre": row["nombre"], "color": row["color"]})
            
            if not tipos:
                from src.utils.constants import FALLAS_DEFAULT, COLORES_DEFAULT
                return [
                    {"nombre": FALLAS_DEFAULT[i], "color": list(COLORES_DEFAULT.values())[i+3]} 
                    for i in range(min(5, len(FALLAS_DEFAULT)))
                ]
            
            logger.info(f"Cargados {len(tipos)} tipos de falla")
            return tipos
        except Exception as e:
            logger.error(f"Error cargando tipos: {e}")
            if conn:
                conn.close()
            from src.utils.constants import FALLAS_DEFAULT, COLORES_DEFAULT
            return [
                {"nombre": FALLAS_DEFAULT[i], "color": list(COLORES_DEFAULT.values())[i+3]} 
                for i in range(min(5, len(FALLAS_DEFAULT)))
            ]

    def guardar_tipos_falla(self, tipos: List[Dict]) -> bool:
        """Guarda los tipos de falla en MySQL"""
        conn = self.db.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tipos_falla")
            
            for i, tipo in enumerate(tipos):
                cursor.execute(
                    "INSERT INTO tipos_falla (nombre, color, orden) VALUES (%s, %s, %s)",
                    (tipo["nombre"], tipo["color"], i)
                )
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info(f"Guardados {len(tipos)} tipos de falla")
            return True
        except Exception as e:
            logger.error(f"Error guardando tipos: {e}")
            if conn:
                conn.rollback()
                conn.close()
            return False

    # ===== MAPEO DE BOTONES =====
    
    def cargar_mapeo_botones(self) -> Dict[int, str]:
        """Carga el mapeo de botones desde MySQL"""
        mapeo = {}
        conn = self.db.get_connection()
        if not conn:
            return mapeo
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT numero_boton, tipo_falla FROM mapeo_botones")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            
            for row in rows:
                mapeo[row[0]] = row[1]
            
            logger.info(f"Mapeo de botones cargado: {len(mapeo)} reglas")
        except Exception as e:
            logger.error(f"Error cargando mapeo: {e}")
            if conn:
                conn.close()
        
        return mapeo

    def guardar_mapeo_botones(self, mapeo_dict: Dict[int, str]) -> bool:
        """Guarda el mapeo de botones en MySQL"""
        conn = self.db.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM mapeo_botones")
            
            for numero, tipo in mapeo_dict.items():
                cursor.execute(
                    "INSERT INTO mapeo_botones (numero_boton, tipo_falla) VALUES (%s, %s)",
                    (numero, tipo)
                )
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info(f"Mapeo de botones guardado: {len(mapeo_dict)} reglas")
            return True
        except Exception as e:
            logger.error(f"Error guardando mapeo: {e}")
            if conn:
                conn.rollback()
                conn.close()
            return False