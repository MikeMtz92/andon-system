# src/controllers/app_controller.py

import logging
import threading
import atexit
import signal
import sys
from datetime import datetime
from typing import Optional

from src.models.database import Database
from src.models.config_model import ConfigModel
from src.models.falla_model import FallaModel
from src.models.licencia_model import LicenciaModel

from src.controllers.licencia_controller import LicenciaController
from src.controllers.falla_controller import FallaController

from src.services.theme_service import ThemeService
from src.services.network_service import NetworkService
from src.services.serial_service import SerialService
from src.services.excel_service import ExcelService

from src.utils.constants import DB_CONFIG_DEFAULT, DB_CONFIG_FILE

logger = logging.getLogger(__name__)

class AppController:
    """Controlador principal de la aplicación"""
    
    def __init__(self):
        # Modelos
        self.db = Database()
        self.config_model = None
        self.falla_model = None
        self.licencia_model = None
        
        # Controladores
        self.licencia_controller = None
        self.falla_controller = None
        
        # Servicios
        self.theme_service = ThemeService()
        self.network_service = NetworkService()
        self.serial_service = SerialService()
        self.excel_service = ExcelService(self.theme_service)
        
        # Configuración
        self.db_config = None
        self.config_sistema = None
        self.config_proyeccion = None
        
        # Estado
        self.installation_id = None
        self.running = True
        
        # Vistas (se asignarán después)
        self.main_view = None
        
        # Configurar cierre
        self._setup_shutdown_handlers()

    def initialize(self) -> bool:
        """Inicializa todos los componentes"""
        try:
            # 1. Cargar configuración de BD
            self.db_config = ConfigModel.cargar_config_db()
            
            # 2. Inicializar pool de conexiones
            if not self.db.initialize(self.db_config):
                logger.error("No se pudo inicializar la base de datos")
                return False
            
            # 3. Inicializar modelos
            self.config_model = ConfigModel(self.db)
            self.falla_model = FallaModel(self.db)
            self.licencia_model = LicenciaModel(self.db)
            
            # 4. Inicializar controladores
            self.licencia_controller = LicenciaController(self.licencia_model, self.config_model)
            self.licencia_controller.cargar_licencia()
            
            self.falla_controller = FallaController(self.falla_model, self.config_model, self.licencia_controller)
            self.falla_controller.cargar_estado_inicial()
            self.falla_controller.on_fallas_actualizadas = self._notificar_actualizacion_fallas
            
            # 5. Cargar configuraciones
            self.config_sistema = self.config_model.cargar_config_sistema()
            self.theme_service.cargar_desde_config(self.config_sistema)
            
            self.config_proyeccion = self.config_model.cargar_config_proyeccion()
            
            # 6. Generar ID de instalación
            import hashlib
            import os
            computer_name = os.environ.get('COMPUTERNAME', 'unknown')
            self.installation_id = hashlib.md5(computer_name.encode()).hexdigest()[:12].upper()
            
            logger.info("Controlador principal inicializado")
            return True
            
        except Exception as e:
            logger.error(f"Error inicializando controlador: {e}")
            return False

    def start_services(self):
        """Inicia los servicios de red y serial"""
        self.network_service.start(self._on_network_event)
        self.serial_service.start(self._on_serial_event)
        
        # Iniciar actualización automática
        self._iniciar_actualizacion_automatica()

    def _on_network_event(self, batch):
        """Callback para eventos de red"""
        for maquina, identificador in batch:
            self.falla_controller.registrar_evento(maquina, identificador)

    def _on_serial_event(self, maquina, identificador):
        """Callback para eventos seriales"""
        self.falla_controller.registrar_evento(maquina, identificador)

    def _notificar_actualizacion_fallas(self):
        """Notifica a las vistas que las fallas han cambiado"""
        if self.main_view and hasattr(self.main_view, 'actualizar_fallas'):
            self.main_view.actualizar_fallas()

    def _iniciar_actualizacion_automatica(self):
        """Inicia el temporizador para actualización automática"""
        def actualizar():
            if not self.running:
                return
            
            try:
                # Recargar fallas desde BD
                nuevas_fallas = self.falla_model.cargar_fallas_activas()
                
                # Comparar y actualizar si hay cambios
                if self._hubo_cambios(self.falla_controller.fallas_activas, nuevas_fallas):
                    self.falla_controller.fallas_activas = nuevas_fallas
                    self._notificar_actualizacion_fallas()
                
            except Exception as e:
                logger.error(f"Error en actualización automática: {e}")
            
            # Programar siguiente actualización
            if self.running:
                import threading
                threading.Timer(60, actualizar).start()
        
        threading.Timer(60, actualizar).start()
        logger.info("Actualización automática iniciada (cada 60s)")

    def _hubo_cambios(self, viejas, nuevas) -> bool:
        """Compara dos listas de fallas para detectar cambios"""
        if len(viejas) != len(nuevas):
            return True
        
        dict_viejo = {(f.get('maquina'), f.get('tipo'), f.get('numero_falla', 0)): f for f in viejas}
        dict_nuevo = {(f.get('maquina'), f.get('tipo'), f.get('numero_falla', 0)): f for f in nuevas}
        
        for key, falla_vieja in dict_viejo.items():
            if key not in dict_nuevo:
                return True
            falla_nueva = dict_nuevo[key]
            for campo in ['estado', 'proceso', 'fin', 'nota_pendiente']:
                if falla_vieja.get(campo) != falla_nueva.get(campo):
                    return True
        return False

    def _setup_shutdown_handlers(self):
        """Configura manejadores para cierre seguro"""
        atexit.register(self.shutdown)
        
        try:
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
        except:
            pass

    def _signal_handler(self, signum, frame):
        logger.info(f"Señal de cierre recibida: {signum}")
        self.shutdown()
        sys.exit(0)

    def shutdown(self):
        """Cierra la aplicación de forma segura"""
        logger.info("Cerrando aplicación...")
        self.running = False
        
        # Detener servicios
        self.network_service.stop()
        self.serial_service.stop()
        
        # Guardar estado
        if self.falla_controller:
            self.falla_controller.guardar_estado()
        
        logger.info("Aplicación cerrada")

    def get_maquinas_permitidas(self) -> list:
        """Retorna la lista de máquinas según licencia"""
        return [str(i) for i in range(1, self.licencia_controller.max_maquinas_permitidas + 1)]

    def get_tipos_falla_limitados(self) -> list:
        """Retorna los tipos de falla limitados según licencia"""
        from src.utils.constants import FALLAS_DEFAULT
        if hasattr(self.falla_controller, 'tipos_falla') and self.falla_controller.tipos_falla:
            return self.falla_controller.tipos_falla[:self.licencia_controller.max_tipos_falla]
        return FALLAS_DEFAULT[:self.licencia_controller.max_tipos_falla]