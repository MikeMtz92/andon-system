# src/utils/constants.py

import hashlib
import os
from datetime import datetime

# ========== CONFIGURACIÓN DE RED ==========
HOST = "0.0.0.0"
PORT = 5000

# ========== CONFIGURACIÓN DE LICENCIAS ==========
LICENSE_DB_CONFIG = {
    "host": "69.6.201.90",
    "port": 3306,
    "usuario": "migue304_licencias_andon",
    "password": "Andon260713.",
    "base_datos": "migue304_licencias_andon",
    "usar_ssl": True,
    "timeout": 30
}

LICENSE_DEFAULTS = {
    "installation_id": hashlib.md5(str(datetime.now()).encode()).hexdigest()[:12].upper(),
    "license_key": "",
    "license_type": "demo",
    "demo_used": False,
    "demo_start": "",
    "demo_expires": "",
    "max_fallas": 3,
    "max_maquinas": 5,
    "last_validation": "",
    "grace_period_start": "",
    "excel_exports_today": 0,
    "last_export_date": ""
}

# ========== ARCHIVOS DE CONFIGURACIÓN ==========
DB_CONFIG_FILE = "db_config.json"

# ========== CONFIGURACIÓN POR DEFECTO ==========
DB_CONFIG_DEFAULT = {
    "tipo": "mysql",
    "host": "localhost",
    "port": 3306,
    "usuario": "root",
    "password": "",
    "base_datos": "andon_db",
    "usar_ssl": False,
    "timeout": 30
}

FALLAS_DEFAULT = ["Mantenimiento", "Producción", "Calidad", "Materiales", "Ingeniería"]
MAQUINAS_DEFAULT = [str(i) for i in range(1, 60)]

PROYECCION_DEFAULT = {
    "pantalla_completa": False,
    "recordar_posicion": True,
    "x": 100,
    "y": 100,
    "ancho": 800,
    "alto": 600,
    "monitor": 0,
    "color_fondo": "#000000",
    "mostrar_contador": True,
    "color_texto": "#FFFFFF",
    "color_acento": "#e94560",
    "color_exito": "#4CAF50",
    "mostrar_pendientes": True
}

CONTADOR_DEFAULT = {
    "ultimo_reset": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "consecutivo_actual": 0,
    "periodo_reset": "diario"
}

# ========== COLORES POR DEFECTO ==========
COLORES_DEFAULT = {
    "fondo": "#1a1a2e",
    "sidebar": "#16213e",
    "card": "#0f3460",
    "texto": "#ffffff",
    "texto_secundario": "#b0b0b0",
    "accento": "#e94560",
    "mantenimiento": "#FF9A00",
    "produccion": "#FF5252",
    "calidad": "#4CAF50",
    "materiales": "#2196F3",
    "ingenieria": "#9C27B0",
    "success": "#00C853",
    "warning": "#FFC107",
    "danger": "#FF5252",
    "negro": "#000000",
    "pendiente": "#FFA500"
}

# ========== TEMAS PREDEFINIDOS ==========
TEMAS_PREDEFINIDOS = {
    "oscuro": {
        "nombre": "🌙 Tema Oscuro (Predeterminado)",
        "colores": {
            "fondo": "#1a1a2e",
            "superficie1": "#16213e",
            "superficie2": "#0f3460",
            "superficie3": "#2d3047",
            "texto_principal": "#ffffff",
            "texto_secundario": "#b0b0b0",
            "acento_principal": "#e94560",
            "exito": "#00C853",
            "advertencia": "#FFC107",
            "peligro": "#FF5252",
            "pendiente": "#FFA500",
        }
    },
    "claro": {
        "nombre": "☀️ Tema Claro",
        "colores": {
            "fondo": "#f5f5f5",
            "superficie1": "#ffffff",
            "superficie2": "#e0e0e0",
            "superficie3": "#d1d1d1",
            "texto_principal": "#212121",
            "texto_secundario": "#757575",
            "acento_principal": "#1976D2",
            "exito": "#2E7D32",
            "advertencia": "#F57C00",
            "peligro": "#C62828",
            "pendiente": "#ED6A02",
        }
    }
}

# ========== ESTADOS DE FALLA ==========
ESTADOS_FALLA = {
    "activa": "🔴 Activa",
    "en_proceso": "🟡 En Proceso",
    "pendiente": "🟠 Pendiente",
    "resuelta": "✅ Resuelta"
}