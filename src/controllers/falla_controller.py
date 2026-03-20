# src/controllers/falla_controller.py

import logging
from datetime import datetime
from typing import List, Dict, Optional, Callable
from src.models.falla_model import FallaModel
from src.models.config_model import ConfigModel
from src.controllers.licencia_controller import LicenciaController
from src.utils.helpers import solo_hora

logger = logging.getLogger(__name__)

class FallaController:
    """Controlador para la lógica de fallas"""
    
    def __init__(self, falla_model: FallaModel, config_model: ConfigModel, 
                 licencia_controller: LicenciaController):
        self.falla_model = falla_model
        self.config_model = config_model
        self.licencia = licencia_controller
        
        self.fallas_activas: List[Dict] = []
        self.mapeo_botones: Dict[int, str] = {}
        self.numeros_falla_asignados = {}
        
        # Callbacks para actualizar vistas
        self.on_fallas_actualizadas: Optional[Callable] = None
        
        # Configuración del contador
        self.config_contador = self.config_model.cargar_config_contador()

    def cargar_estado_inicial(self):
        """Carga fallas activas y mapeo desde la BD"""
        self.fallas_activas = self.falla_model.cargar_fallas_activas()
        self.mapeo_botones = self.falla_model.cargar_mapeo_botones()
        
        # Asignar números de falla si no tienen
        for falla in self.fallas_activas:
            if "numero_falla" not in falla:
                falla["numero_falla"] = self._obtener_siguiente_numero_falla()
            self.numeros_falla_asignados[id(falla)] = falla["numero_falla"]
        
        logger.info(f"Estado inicial cargado: {len(self.fallas_activas)} fallas activas")

    def _obtener_siguiente_numero_falla(self) -> int:
        """Obtiene el siguiente número de falla según la configuración"""
        config = self.config_contador

        if config["periodo_reset"] != "nunca":
            ahora = datetime.now()
            ultimo_reset = datetime.strptime(config["ultimo_reset"], "%Y-%m-%d %H:%M:%S")
            necesita_reset = False

            if config["periodo_reset"] == "horas_12":
                if (ahora - ultimo_reset).total_seconds() >= 12 * 3600:
                    necesita_reset = True
            elif config["periodo_reset"] == "diario":
                if ahora.date() > ultimo_reset.date():
                    necesita_reset = True
            elif config["periodo_reset"] == "semanal":
                if ahora.isocalendar()[1] > ultimo_reset.isocalendar()[1] or ahora.year > ultimo_reset.year:
                    necesita_reset = True
            elif config["periodo_reset"] == "mensual":
                if ahora.month > ultimo_reset.month or ahora.year > ultimo_reset.year:
                    necesita_reset = True
            elif config["periodo_reset"] == "anual":
                if ahora.year > ultimo_reset.year:
                    necesita_reset = True

            if necesita_reset:
                config["consecutivo_actual"] = 0
                config["ultimo_reset"] = ahora.strftime("%Y-%m-%d %H:%M:%S")

        config["consecutivo_actual"] += 1
        self.config_model.guardar_config_contador(config)
        self.config_contador = config
        
        return config["consecutivo_actual"]

    def registrar_evento(self, maquina: str, identificador: str):
        """Registra un evento de falla desde red/serial o UI"""
        logger.debug(f"Evento recibido: máq={maquina}, id={identificador}")
        
        # Verificar límite de máquinas
        if not self.licencia.verificar_limite_maquina(maquina):
            logger.warning(f"Máquina {maquina} excede límite de licencia")
            return

        # Determinar tipo de falla
        if identificador and identificador.startswith("Boton"):
            try:
                numero_boton = int(identificador.replace("Boton", ""))
                tipo_falla = self.mapeo_botones.get(numero_boton)
                if not tipo_falla:
                    logger.warning(f"Botón {numero_boton} no mapeado")
                    return
            except Exception as e:
                logger.error(f"Error procesando botón: {e}")
                return
        else:
            tipo_falla = identificador

        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Buscar falla existente
        falla_existente = None
        for alerta in self.fallas_activas:
            if alerta["maquina"] == maquina and alerta["tipo"] == tipo_falla:
                falla_existente = alerta
                break

        if falla_existente:
            self._procesar_falla_existente(falla_existente, ahora)
        else:
            self._crear_nueva_falla(maquina, tipo_falla, ahora)

        # Notificar a las vistas
        if self.on_fallas_actualizadas:
            self.on_fallas_actualizadas()

    def _procesar_falla_existente(self, falla: Dict, ahora: str):
        """Procesa una falla que ya existe (transición de estado)"""
        estado_actual = falla.get("estado", "activa")
        
        if estado_actual == "activa":
            falla["proceso"] = ahora
            falla["estado"] = "en_proceso"
            self.falla_model.guardar_falla_activa(falla)
            logger.info(f"Falla en proceso: {falla['maquina']} - {falla['tipo']}")
            
        elif estado_actual == "en_proceso":
            falla["fin"] = ahora
            falla["estado"] = "resuelta"
            self.falla_model.guardar_falla_en_historial(falla)
            self.fallas_activas.remove(falla)
            logger.info(f"Falla finalizada: {falla['maquina']} - {falla['tipo']}")
            
        elif estado_actual == "pendiente":
            logger.info("Falla pendiente, requiere acción manual")

    def _crear_nueva_falla(self, maquina: str, tipo: str, ahora: str):
        """Crea una nueva falla"""
        numero_falla = self._obtener_siguiente_numero_falla()
        
        nueva_falla = {
            "maquina": maquina,
            "tipo": tipo,
            "inicio": ahora,
            "numero_falla": numero_falla,
            "estado": "activa"
        }
        
        self.falla_model.guardar_falla_activa(nueva_falla)
        self.fallas_activas.append(nueva_falla)
        logger.info(f"Nueva falla #{numero_falla}: {maquina} - {tipo}")

    def marcar_en_proceso(self, alerta: Dict):
        """Marca una falla como en proceso manualmente"""
        if alerta.get("estado") != "activa":
            return
        
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        alerta["proceso"] = ahora
        alerta["estado"] = "en_proceso"
        self.falla_model.guardar_falla_activa(alerta)
        
        if self.on_fallas_actualizadas:
            self.on_fallas_actualizadas()

    def finalizar_falla(self, alerta: Dict):
        """Finaliza una falla manualmente"""
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if "proceso" not in alerta or not alerta["proceso"]:
            alerta["proceso"] = ahora
        
        alerta["fin"] = ahora
        alerta["estado"] = "resuelta"
        
        self.falla_model.guardar_falla_en_historial(alerta)
        
        if alerta in self.fallas_activas:
            self.fallas_activas.remove(alerta)
        
        if self.on_fallas_actualizadas:
            self.on_fallas_actualizadas()

    def marcar_pendiente(self, alerta: Dict, nota: str):
        """Marca una falla como pendiente con nota"""
        if not self.licencia.puede_usar_pendientes:
            return
        
        alerta["nota_pendiente"] = nota
        alerta["estado"] = "pendiente"
        alerta["fecha_pendiente"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.falla_model.guardar_falla_activa(alerta)
        
        if self.on_fallas_actualizadas:
            self.on_fallas_actualizadas()

    def cerrar_todas_fallas(self):
        """Cierra todas las fallas activas"""
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fallas_a_cerrar = self.fallas_activas.copy()
        
        for alerta in fallas_a_cerrar:
            if "proceso" not in alerta or not alerta["proceso"]:
                alerta["proceso"] = ahora
            alerta["fin"] = ahora
            alerta["estado"] = "resuelta"
            self.falla_model.guardar_falla_en_historial(alerta)
            self.fallas_activas.remove(alerta)
        
        self.falla_model.guardar_fallas_activas(self.fallas_activas)
        
        if self.on_fallas_actualizadas:
            self.on_fallas_actualizadas()
        
        logger.info(f"Cerradas {len(fallas_a_cerrar)} fallas")

    def get_fallas_pendientes(self) -> List[Dict]:
        """Retorna solo las fallas pendientes"""
        return [a for a in self.fallas_activas if a.get("estado") == "pendiente"]

    def get_estadisticas(self) -> Dict:
        """Retorna estadísticas básicas"""
        return {
            "activas": len(self.fallas_activas),
            "en_proceso": sum(1 for a in self.fallas_activas if a.get("estado") == "en_proceso"),
            "pendientes": len(self.get_fallas_pendientes())
        }

    def guardar_estado(self):
        """Guarda el estado actual en BD"""
        self.falla_model.guardar_fallas_activas(self.fallas_activas)

    def actualizar_mapeo(self, nuevo_mapeo: Dict[int, str]):
        """Actualiza el mapeo de botones"""
        self.mapeo_botones = nuevo_mapeo
        self.falla_model.guardar_mapeo_botones(nuevo_mapeo)