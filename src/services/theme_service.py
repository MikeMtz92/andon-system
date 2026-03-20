# src/services/theme_service.py

import logging
from typing import Dict
from src.utils.constants import COLORES_DEFAULT, TEMAS_PREDEFINIDOS
from src.utils.helpers import is_light_color

logger = logging.getLogger(__name__)

class ThemeService:
    """Servicio para gestionar temas y colores de la interfaz"""
    
    def __init__(self):
        self.colores = COLORES_DEFAULT.copy()
        self.tema_actual = "oscuro"
        self.paleta_actual = TEMAS_PREDEFINIDOS["oscuro"]["colores"].copy()
        self._actualizar_mapeos()

    def _actualizar_mapeos(self):
        """Actualiza los mapeos de compatibilidad"""
        self.colores.update({
            "sidebar": self.paleta_actual.get("superficie1", "#16213e"),
            "card": self.paleta_actual.get("superficie2", "#0f3460"),
            "texto": self.paleta_actual.get("texto_principal", "#ffffff"),
            "texto_secundario": self.paleta_actual.get("texto_secundario", "#b0b0b0"),
            "accento": self.paleta_actual.get("acento_principal", "#e94560"),
            "exito": self.paleta_actual.get("exito", "#00C853"),
            "warning": self.paleta_actual.get("advertencia", "#FFC107"),
            "danger": self.paleta_actual.get("peligro", "#FF5252"),
            "pendiente": self.paleta_actual.get("pendiente", "#FFA500"),
            "fondo": self.paleta_actual.get("fondo", "#1a1a2e"),
            "superficie3": self.paleta_actual.get("superficie3", "#2d3047")
        })

    def cargar_desde_config(self, config_sistema: dict):
        """Carga la configuración de colores desde un diccionario"""
        tema_activo = config_sistema.get("tema_activo", "oscuro")
        
        if tema_activo in TEMAS_PREDEFINIDOS:
            self.tema_actual = tema_activo
            self.paleta_actual = TEMAS_PREDEFINIDOS[tema_activo]["colores"].copy()
        else:
            self.tema_actual = "personalizado"
            self.paleta_actual = {
                "fondo": config_sistema.get("color_fondo", "#1a1a2e"),
                "superficie1": config_sistema.get("color_sidebar", "#16213e"),
                "superficie2": config_sistema.get("color_card", "#0f3460"),
                "superficie3": config_sistema.get("superficie3", "#2d3047"),
                "texto_principal": config_sistema.get("texto_principal", "#ffffff"),
                "texto_secundario": config_sistema.get("texto_secundario", "#b0b0b0"),
                "acento_principal": config_sistema.get("acento_principal", "#e94560"),
                "exito": config_sistema.get("exito", "#00C853"),
                "advertencia": config_sistema.get("advertencia", "#FFC107"),
                "peligro": config_sistema.get("peligro", "#FF5252"),
                "pendiente": config_sistema.get("pendiente", "#FFA500")
            }
        
        self._actualizar_mapeos()
        logger.info(f"Tema cargado: {self.tema_actual}")

    def aplicar_tema(self, tema_nombre: str):
        """Aplica un tema predefinido"""
        if tema_nombre in TEMAS_PREDEFINIDOS:
            self.tema_actual = tema_nombre
            self.paleta_actual = TEMAS_PREDEFINIDOS[tema_nombre]["colores"].copy()
            self._actualizar_mapeos()
            logger.info(f"Tema aplicado: {tema_nombre}")
            return True
        return False

    def actualizar_color(self, clave_paleta: str, color_hex: str):
        """Actualiza un color específico"""
        self.paleta_actual[clave_paleta] = color_hex
        self.tema_actual = "personalizado"
        self._actualizar_mapeos()

    def get_color_para_tipo(self, tipo: str) -> str:
        """Obtiene el color asociado a un tipo de falla"""
        # 1. Buscar en colores guardados
        tipo_color_key = f"{tipo.lower().replace(' ', '_')}_color"
        
        if tipo_color_key in self.colores:
            return self.colores[tipo_color_key]
        
        # 2. Buscar en la paleta de colores de tipos (si existe)
        # Esto debería venir de la base de datos
        try:
            from src.models.falla_model import FallaModel
            # Esto es un poco hacky, pero funciona
            tipos_data = FallaModel(None).cargar_tipos_falla()
            for t in tipos_data:
                if t["nombre"] == tipo:
                    return t["color"]
        except:
            pass
        
        # 3. Fallback a colores base
        colores_base = {
            "mantenimiento": "#FF9A00",
            "producción": "#FF5252",
            "produccion": "#FF5252",
            "calidad": "#4CAF50",
            "materiales": "#2196F3",
            "ingeniería": "#9C27B0",
            "ingenieria": "#9C27B0"
        }
        
        tipo_lower = tipo.lower()
        for key, color in colores_base.items():
            if tipo_lower == key:
                return color
        
        # 4. Último recurso: color aleatorio basado en hash
        import hashlib
        hash_obj = hashlib.md5(tipo.encode())
        hash_int = int(hash_obj.hexdigest(), 16)
        hue = (hash_int % 360) / 360.0
        from colorsys import hsv_to_rgb
        r, g, b = hsv_to_rgb(hue, 0.7, 0.6)
        return f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'

    def generar_config_sistema(self) -> dict:
        """Genera un diccionario config_sistema a partir de la paleta actual"""
        return {
            "nombre_sistema": self.colores.get("nombre_sistema", "ANDON SYSTEM"),
            "tema_activo": self.tema_actual,
            "color_fondo": self.paleta_actual.get("fondo", "#1a1a2e"),
            "color_sidebar": self.paleta_actual.get("superficie1", "#16213e"),
            "color_card": self.paleta_actual.get("superficie2", "#0f3460"),
            "superficie3": self.paleta_actual.get("superficie3", "#2d3047"),
            "color_texto": self.paleta_actual.get("texto_principal", "#ffffff"),
            "texto_principal": self.paleta_actual.get("texto_principal", "#ffffff"),
            "color_texto_secundario": self.paleta_actual.get("texto_secundario", "#b0b0b0"),
            "texto_secundario": self.paleta_actual.get("texto_secundario", "#b0b0b0"),
            "color_acento": self.paleta_actual.get("acento_principal", "#e94560"),
            "acento_principal": self.paleta_actual.get("acento_principal", "#e94560"),
            "color_exito": self.paleta_actual.get("exito", "#00C853"),
            "exito": self.paleta_actual.get("exito", "#00C853"),
            "color_warning": self.paleta_actual.get("advertencia", "#FFC107"),
            "advertencia": self.paleta_actual.get("advertencia", "#FFC107"),
            "color_danger": self.paleta_actual.get("peligro", "#FF5252"),
            "peligro": self.paleta_actual.get("peligro", "#FF5252"),
            "color_pendiente": self.paleta_actual.get("pendiente", "#FFA500"),
            "pendiente": self.paleta_actual.get("pendiente", "#FFA500")
        }