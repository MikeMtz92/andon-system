# src/utils/helpers.py

from colorsys import rgb_to_hls, hls_to_rgb
import hashlib
from datetime import datetime

def is_light_color(hex_color):
    """Determina si un color es claro para elegir texto blanco o negro"""
    if hex_color.startswith('#'):
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    else:
        rgb = hex_color
    luminance = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255
    return luminance > 0.5

def lighten_color(color, factor=0.2):
    """Aclara un color dado"""
    if isinstance(color, str) and color.startswith('#'):
        color = color.lstrip('#')
        rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
    else:
        rgb = color
    h, l, s = rgb_to_hls(rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0)
    l = min(1.0, l + factor)
    r, g, b = hls_to_rgb(h, l, s)
    return f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'

def get_installation_id():
    """Genera un ID de instalación basado en el nombre del equipo"""
    computer_name = os.environ.get('COMPUTERNAME', 'unknown')
    return hashlib.md5(computer_name.encode()).hexdigest()[:12].upper()

def solo_hora(fecha_completa):
    """Extrae solo la hora de una fecha completa"""
    if not fecha_completa:
        return ""
    try:
        if len(fecha_completa) <= 8 and ":" in fecha_completa:
            return fecha_completa
        return datetime.strptime(fecha_completa, "%Y-%m-%d %H:%M:%S").strftime("%H:%M:%S")
    except:
        return fecha_completa if fecha_completa else ""