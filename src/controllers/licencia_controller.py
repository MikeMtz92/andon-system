# src/controllers/licencia_controller.py

import logging
from datetime import datetime  # <-- AÑADIR ESTA LÍNEA
from typing import Dict, Tuple, Optional
from src.models.licencia_model import LicenciaModel
from src.models.config_model import ConfigModel
from src.utils.constants import LICENSE_DEFAULTS

logger = logging.getLogger(__name__)

class LicenciaController:
    """Controlador para la lógica de licenciamiento"""
    
    def __init__(self, licencia_model: LicenciaModel, config_model: ConfigModel):
        self.licencia_model = licencia_model
        self.config_model = config_model
        self.config = None
        self.licencia_valida = False
        
        # Límites por defecto
        self.max_tipos_falla = 3
        self.max_maquinas_permitidas = 5
        self.puede_configurar = False
        self.puede_ver_graficos = False
        self.puede_exportar_excel_con_graficos = False
        self.excel_una_vez_dia = False
        self.puede_generar_esp32 = False
        self.puede_configurar_proyeccion = False
        self.recupera_fallas = False
        self.reset_consecutivo = "diario"
        self.puede_usar_pendientes = False
        self.puede_agregar_notas = False
        self.puede_ver_pendientes = False
        self.puede_filtrar_tipos_graficas = False
        self.puede_ajustar_periodo_estadisticas = False
        self.dias_tendencia_predeterminados = 7
        self.puede_usar_mysql = True

    def cargar_licencia(self):
        """Carga la licencia desde la BD"""
        self.config = self.licencia_model.cargar_config_licencia()
        self._verificar_y_aplicar()
        return self.config

    def _verificar_y_aplicar(self):
        """Verifica el estado y aplica los límites"""
        valida, info = self.licencia_model.verificar_estado_licencia(self.config)
        self.licencia_valida = valida
        
        if valida:
            self._aplicar_limites_por_tipo(info.get('license_type', 'basic') if isinstance(info, dict) else self.config.get('license_type', 'basic'))
        else:
            logger.warning(f"Licencia no válida: {info}")

    def _aplicar_limites_por_tipo(self, tipo: str):
        """Aplica los límites según el tipo de licencia"""
        if tipo == 'basic':
            self.max_tipos_falla = self.config.get('max_fallas', 3)
            self.max_maquinas_permitidas = self.config.get('max_maquinas', 5)
            self.puede_configurar = False
            self.puede_ver_graficos = False
            self.puede_exportar_excel_con_graficos = False
            self.excel_una_vez_dia = False
            self.puede_generar_esp32 = False
            self.puede_configurar_proyeccion = False
            self.recupera_fallas = False  # BASIC NO recupera fallas
            self.reset_consecutivo = "diario"
            self.puede_usar_pendientes = False
            self.puede_agregar_notas = False
            self.puede_ver_pendientes = False
            self.puede_filtrar_tipos_graficas = False
            self.puede_ajustar_periodo_estadisticas = False

        elif tipo == 'mid':
            self.max_tipos_falla = self.config.get('max_fallas', 4)
            self.max_maquinas_permitidas = self.config.get('max_maquinas', 15)
            self.puede_configurar = True
            self.puede_ver_graficos = True
            self.puede_exportar_excel_con_graficos = True
            self.excel_una_vez_dia = False
            self.puede_generar_esp32 = False
            self.puede_configurar_proyeccion = True
            self.recupera_fallas = True  # MID recupera fallas
            self.reset_consecutivo = "configurable"
            self.puede_usar_pendientes = True
            self.puede_agregar_notas = False
            self.puede_ver_pendientes = True
            self.puede_filtrar_tipos_graficas = False
            self.puede_ajustar_periodo_estadisticas = False

        elif tipo in ['pro', 'demo']:
            self.max_tipos_falla = self.config.get('max_fallas', 5)
            self.max_maquinas_permitidas = self.config.get('max_maquinas', 200)
            self.puede_configurar = True
            self.puede_ver_graficos = True
            self.puede_exportar_excel_con_graficos = True
            self.excel_una_vez_dia = False
            self.puede_generar_esp32 = True
            self.puede_configurar_proyeccion = True
            self.recupera_fallas = True  # PRO recupera fallas
            self.reset_consecutivo = "configurable"
            self.puede_usar_pendientes = True
            self.puede_agregar_notas = True
            self.puede_ver_pendientes = True
            self.puede_filtrar_tipos_graficas = True
            self.puede_ajustar_periodo_estadisticas = True

        logger.info(f"Límites aplicados para licencia {tipo}")

    def verificar_limite_maquina(self, maquina: str) -> bool:
        """Verifica si una máquina está dentro del límite"""
        if self.config.get('license_type') == 'pro':
            return True
        
        try:
            num_maquina = int(maquina)
            if num_maquina > self.max_maquinas_permitidas:
                return False
        except:
            pass
        return True

    def verificar_limite_excel(self) -> bool:
        """Verifica si se puede exportar Excel según límite diario"""
        if self.config.get('license_type') == 'pro':
            return True

        hoy = datetime.now().strftime("%Y-%m-%d")
        if self.config.get('last_export_date') != hoy:
            self.config['excel_exports_today'] = 0
            self.config['last_export_date'] = hoy

        if self.config.get('license_type') == 'mid' and self.config.get('excel_exports_today', 0) >= 1:
            return False

        return True

    def registrar_export_excel(self):
        """Registra una exportación de Excel"""
        hoy = datetime.now().strftime("%Y-%m-%d")
        if self.config.get('last_export_date') != hoy:
            self.config['excel_exports_today'] = 0
            self.config['last_export_date'] = hoy
        
        self.config['excel_exports_today'] = self.config.get('excel_exports_today', 0) + 1
        self.licencia_model.guardar_config_licencia(self.config)

    def activar_licencia(self, license_key: str, installation_id: str) -> Tuple[bool, str]:
        """Activa una licencia con validación online"""
        valido, info = self.licencia_model.validar_licencia_online(license_key, installation_id)
        
        if valido:
            self.config.update({
                'license_key': license_key,
                'license_type': info['license_type'],
                'max_fallas': info['max_fallas'],
                'max_maquinas': info['max_maquinas'],
                'last_validation': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'expires_at': info['expires_at'],
                'demo_used': False,  # Limpiar demo si existía
                'demo_start': "",
                'demo_expires': ""
            })
            self.licencia_model.guardar_config_licencia(self.config)
            self._aplicar_limites_por_tipo(info['license_type'])
            return True, f"Licencia {info['license_type']} activada"
        
        return False, info

    def iniciar_demo(self, installation_id: str) -> Tuple[bool, str]:
        """Inicia un periodo de demo"""
        if self.config.get('demo_used'):
            return False, "Ya has utilizado el periodo de demo"
        
        exito, info = self.licencia_model.iniciar_demo(installation_id)
        
        if exito:
            self.config.update({
                'demo_used': True,
                'demo_start': datetime.now().strftime("%Y-%m-%d"),
                'demo_expires': info,
                'license_type': 'demo',
                'license_key': ""  # Limpiar licencia si existía
            })
            self.licencia_model.guardar_config_licencia(self.config)
            self._aplicar_limites_por_tipo('demo')
            return True, info
        
        return False, info

    def desactivar_licencia(self):
        """Vuelve al modo básico"""
        self.config.update({
            'license_key': "",
            'license_type': "basic",
            'max_fallas': 3,
            'max_maquinas': 5,
            'last_validation': "",
            'demo_used': False,
            'demo_expires': "",
            'expires_at': ""
        })
        self.licencia_model.guardar_config_licencia(self.config)
        self._aplicar_limites_por_tipo('basic')