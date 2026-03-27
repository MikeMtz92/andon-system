import tkinter as tk
from tkinter import messagebox, ttk, filedialog, colorchooser
from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import Error
import threading
import winsound
import pandas as pd
import matplotlib.pyplot as plt
from tkcalendar import DateEntry
from openpyxl import load_workbook
from openpyxl.drawing.image import Image as ExcelImage
import io
import serial
import serial.tools.list_ports
import socket
import json
import os
import atexit
import signal
import hashlib
from colorsys import rgb_to_hls, hls_to_rgb, hsv_to_rgb
import psutil 
import time
import queue

# ========== CONFIGURACIÓN INICIAL ==========
HOST = "0.0.0.0"
PORT = 5000

FALLAS_DEFAULT = ["Mantenimiento", "Producción", "Calidad", "Materiales", "Ingeniería"]
FALLAS = ["Mantenimiento", "Producción", "Calidad", "Materiales", "Ingeniería"]
MAQUINAS = [str(i) for i in range(1, 60)]

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
    "negro": "#000000"
}

# ========== CONFIGURACIÓN DE TEMAS ==========
TEMAS_PREDEFINIDOS = {
    "oscuro": {
        "nombre": "🌙 Tema Oscuro (Predeterminado)",
        "colores": {
            "fondo": "#1a1a2e",        # Fondo principal muy oscuro
            "superficie1": "#16213e",   # Sidebar, tarjetas elevadas
            "superficie2": "#0f3460",   # Tarjetas, frames internos
            "superficie3": "#2d3047",   # Entradas de texto, inputs
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
            "fondo": "#f5f5f5",        # Fondo principal claro
            "superficie1": "#ffffff",    # Sidebar, tarjetas elevadas (blanco)
            "superficie2": "#e0e0e0",    # Tarjetas, frames internos (gris claro)
            "superficie3": "#d1d1d1",    # Entradas de texto (gris un poco más oscuro)
            "texto_principal": "#212121",
            "texto_secundario": "#757575",
            "acento_principal": "#1976D2", # Un azul vibrante
            "exito": "#2E7D32",           # Verde oscuro
            "advertencia": "#F57C00",     # Naranja
            "peligro": "#C62828",         # Rojo oscuro
            "pendiente": "#ED6A02",       # Naranja oscuro
        }
    }
}

DB_CONFIG_FILE = "db_config.json"  # Este archivo se mantiene para la config de conexión a MySQL

# Configuración por defecto de la base de datos
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

# Configuración por defecto para la proyección
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
    "color_exito": "#4CAF50"
}

# Configuración del contador de fallas
CONTADOR_DEFAULT = {
    "ultimo_reset": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "consecutivo_actual": 0,
    "periodo_reset": "diario",
    "ultimo_numero_usado": 0
}

# ========== SISTEMA DE LICENCIAMIENTO ==========
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

# Después de las otras constantes (alrededor de línea 60)
ESTADOS_FALLA = {
    "activa": "🔴 Activa",
    "en_proceso": "🟡 En Proceso",
    "pendiente": "🟠 Pendiente",  # Nuevo estado
    "resuelta": "✅ Resuelta"
}

# Colores para el estado pendiente
COLORES_DEFAULT["pendiente"] = "#FFA500"  # Naranja



# ============================================================================
# ========== FUNCIONES DE ACCESO A BASE DE DATOS (CONFIGURACIÓN) ==========
# ============================================================================

# --- Funciones genéricas de lectura/escritura en BD ---

def obtener_conexion_mysql(db_config, timeout=5):
    """
    Obtiene una conexión a MySQL si está disponible.
    Ahora con timeout configurable y mejor manejo de errores.
    """
    if db_config.get("tipo") != "mysql":
        print("❌ Error: Intentando conectar a MySQL pero el tipo de BD no es 'mysql'")
        return None
    
    try:
        conn = mysql.connector.connect(
            host=db_config["host"],
            port=db_config["port"],
            user=db_config["usuario"],
            password=db_config["password"],
            database=db_config["base_datos"],
            connection_timeout=timeout,
            ssl_disabled=not db_config.get("usar_ssl", False),
            use_pure=True,
            autocommit=False,
            buffered=True,
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
        return conn
    except mysql.connector.Error as e:
        print(f"❌ Error conectando a MySQL: {e}")
        return None
    except Exception as e:
        print(f"❌ Error inesperado conectando a MySQL: {e}")
        return None
    


    
# ========== FUNCIONES PARA MAPEO DE BOTONES (NUEVO) ==========
def cargar_mapeo_botones(db_config):
    """Carga el mapeo de número de botón a tipo de falla desde MySQL"""
    mapeo = {}
    
    if db_config.get("tipo") != "mysql":
        print("❌ Error: cargar_mapeo_botones solo funciona con MySQL")
        return mapeo
    
    conn = obtener_conexion_mysql(db_config, timeout=5)
    if not conn:
        print("⚠️ No se pudo conectar a MySQL para cargar mapeo de botones")
        return mapeo
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT numero_boton, tipo_falla FROM mapeo_botones")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        for row in rows:
            mapeo[row[0]] = row[1]
        
        print(f"✅ Mapeo de botones cargado desde MySQL: {len(mapeo)} reglas")
    except Exception as e:
        print(f"⚠️ Error cargando mapeo_botones: {e}")
        if conn:
            conn.close()
    
    return mapeo

def guardar_mapeo_botones(mapeo_dict, db_config):
    """Guarda el mapeo de botones en MySQL"""
    if db_config.get("tipo") != "mysql":
        print("❌ Error: guardar_mapeo_botones solo funciona con MySQL")
        return False
    
    conn = obtener_conexion_mysql(db_config)
    if not conn:
        print("❌ No se pudo conectar a MySQL para guardar mapeo de botones")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Limpiar tabla
        cursor.execute("DELETE FROM mapeo_botones")
        
        # Insertar nuevos valores
        for numero_boton, tipo_falla in mapeo_dict.items():
            cursor.execute(
                "INSERT INTO mapeo_botones (numero_boton, tipo_falla) VALUES (%s, %s)",
                (numero_boton, tipo_falla)
            )
        
        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ Mapeo de botones guardado en MySQL: {len(mapeo_dict)} reglas")
        return True
    except Exception as e:
        print(f"❌ Error guardando mapeo_botones: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False
    
# --- FUNCIONES PARA CONFIG_SISTEMA ---
def cargar_config_sistema(db_config):
    """Carga la configuración del sistema desde MySQL"""
    config = {
        "nombre_sistema": "ANDON SYSTEM",
        "tema_activo": "oscuro",
        "color_fondo": "#1a1a2e",
        "color_sidebar": "#16213e",
        "color_card": "#0f3460",
        "superficie3": "#2d3047",
        "color_texto": "#ffffff",
        "texto_principal": "#ffffff",
        "color_texto_secundario": "#b0b0b0",
        "texto_secundario": "#b0b0b0",
        "color_acento": "#e94560",
        "acento_principal": "#e94560",
        "color_exito": "#00C853",
        "exito": "#00C853",
        "color_warning": "#FFC107",
        "advertencia": "#FFC107",
        "color_danger": "#FF5252",
        "peligro": "#FF5252",
        "color_pendiente": "#FFA500",
        "pendiente": "#FFA500"
    }
    
    # Verificar que sea MySQL
    if db_config.get("tipo") != "mysql":
        print("❌ Error: cargar_config_sistema solo funciona con MySQL")
        return config
    
    conn = obtener_conexion_mysql(db_config, timeout=5)
    if not conn:
        print("⚠️ No se pudo conectar a MySQL, usando valores por defecto")
        return config
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM config_sistema WHERE id = 1")
        row = cursor.fetchone()
        if row:
            for key in config.keys():
                if key in row and row[key] is not None:
                    config[key] = row[key]
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"⚠️ Error cargando config_sistema de MySQL: {e}")
        if conn:
            conn.close()
    
    return config

def guardar_config_sistema(config, db_config):
    """Guarda la configuración del sistema en MySQL"""
    if db_config.get("tipo") != "mysql":
        print("❌ Error: guardar_config_sistema solo funciona con MySQL")
        return False
    
    conn = obtener_conexion_mysql(db_config)
    if not conn:
        print("❌ No se pudo conectar a MySQL para guardar configuración")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Verificar si la tabla tiene las columnas nuevas
        cursor.execute("SHOW COLUMNS FROM config_sistema")
        columnas_existentes = [col[0] for col in cursor.fetchall()]
        
        # Primero verificar si ya existe el registro
        cursor.execute("SELECT id FROM config_sistema WHERE id = 1")
        existe = cursor.fetchone()
        
        # Preparar la consulta dinámicamente según las columnas existentes
        campos = []
        valores = []
        
        # Campos siempre presentes
        campos.append("nombre_sistema = %s")
        valores.append(config.get("nombre_sistema", "ANDON SYSTEM"))
        
        # Tema activo
        if "tema_activo" in columnas_existentes:
            campos.append("tema_activo = %s")
            valores.append(config.get("tema_activo", "oscuro"))
        
        # Colores principales
        if "color_fondo" in columnas_existentes:
            campos.append("color_fondo = %s")
            valores.append(config.get("color_fondo", "#1a1a2e"))
        
        if "color_sidebar" in columnas_existentes:
            campos.append("color_sidebar = %s")
            valores.append(config.get("color_sidebar", "#16213e"))
        
        if "color_card" in columnas_existentes:
            campos.append("color_card = %s")
            valores.append(config.get("color_card", "#0f3460"))
        
        # Nuevas columnas
        if "superficie3" in columnas_existentes:
            campos.append("superficie3 = %s")
            valores.append(config.get("superficie3", "#2d3047"))
        
        if "color_texto" in columnas_existentes:
            campos.append("color_texto = %s")
            valores.append(config.get("color_texto", "#ffffff"))
        
        if "texto_principal" in columnas_existentes:
            campos.append("texto_principal = %s")
            valores.append(config.get("texto_principal", "#ffffff"))
        
        if "color_texto_secundario" in columnas_existentes:
            campos.append("color_texto_secundario = %s")
            valores.append(config.get("color_texto_secundario", "#b0b0b0"))
        
        if "texto_secundario" in columnas_existentes:
            campos.append("texto_secundario = %s")
            valores.append(config.get("texto_secundario", "#b0b0b0"))
        
        if "color_acento" in columnas_existentes:
            campos.append("color_acento = %s")
            valores.append(config.get("color_acento", "#e94560"))
        
        if "acento_principal" in columnas_existentes:
            campos.append("acento_principal = %s")
            valores.append(config.get("acento_principal", "#e94560"))
        
        if "color_exito" in columnas_existentes:
            campos.append("color_exito = %s")
            valores.append(config.get("color_exito", "#00C853"))
        
        if "exito" in columnas_existentes:
            campos.append("exito = %s")
            valores.append(config.get("exito", "#00C853"))
        
        if "color_warning" in columnas_existentes:
            campos.append("color_warning = %s")
            valores.append(config.get("color_warning", "#FFC107"))
        
        if "advertencia" in columnas_existentes:
            campos.append("advertencia = %s")
            valores.append(config.get("advertencia", "#FFC107"))
        
        if "color_danger" in columnas_existentes:
            campos.append("color_danger = %s")
            valores.append(config.get("color_danger", "#FF5252"))
        
        if "peligro" in columnas_existentes:
            campos.append("peligro = %s")
            valores.append(config.get("peligro", "#FF5252"))
        
        if "color_pendiente" in columnas_existentes:
            campos.append("color_pendiente = %s")
            valores.append(config.get("color_pendiente", "#FFA500"))
        
        if "pendiente" in columnas_existentes:
            campos.append("pendiente = %s")
            valores.append(config.get("pendiente", "#FFA500"))
        
        if existe:
            # Actualizar registro existente
            query = f"UPDATE config_sistema SET {', '.join(campos)} WHERE id = 1"
            cursor.execute(query, valores)
            print("✅ Configuración del sistema actualizada en MySQL")
        else:
            # Insertar nuevo registro
            campos_insert = ["id"] + [c.split(" = ")[0] for c in campos]
            placeholders = ["%s"] * len(campos_insert)
            valores_insert = [1] + valores
            
            query_insert = f"INSERT INTO config_sistema ({', '.join(campos_insert)}) VALUES ({', '.join(placeholders)})"
            cursor.execute(query_insert, valores_insert)
            print("✅ Configuración del sistema insertada en MySQL")
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error guardando config_sistema en MySQL: {e}")
        if conn:
            conn.rollback()
            conn.close()
        import traceback
        traceback.print_exc()
        return False
                   
# --- FUNCIONES PARA TIPOS_FALLA ---
def cargar_tipos_falla(db_config):
    """Carga la lista de tipos de falla desde MySQL"""
    tipos = []
    
    if db_config.get("tipo") != "mysql":
        print("❌ Error: cargar_tipos_falla solo funciona con MySQL")
        # Devolver valores por defecto como fallback
        return [
            {"nombre": "Mantenimiento", "color": "#FF9A00"},
            {"nombre": "Producción", "color": "#FF5252"},
            {"nombre": "Calidad", "color": "#4CAF50"},
            {"nombre": "Materiales", "color": "#2196F3"},
            {"nombre": "Ingeniería", "color": "#9C27B0"}
        ]
    
    conn = obtener_conexion_mysql(db_config, timeout=5)
    if not conn:
        print("⚠️ No se pudo conectar a MySQL para cargar tipos, usando valores por defecto")
        return [
            {"nombre": "Mantenimiento", "color": "#FF9A00"},
            {"nombre": "Producción", "color": "#FF5252"},
            {"nombre": "Calidad", "color": "#4CAF50"},
            {"nombre": "Materiales", "color": "#2196F3"},
            {"nombre": "Ingeniería", "color": "#9C27B0"}
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
            print("⚠️ No hay tipos de falla en la BD, usando valores por defecto")
            return [
                {"nombre": "Mantenimiento", "color": "#FF9A00"},
                {"nombre": "Producción", "color": "#FF5252"},
                {"nombre": "Calidad", "color": "#4CAF50"},
                {"nombre": "Materiales", "color": "#2196F3"},
                {"nombre": "Ingeniería", "color": "#9C27B0"}
            ]
        
        print(f"✅ Cargados {len(tipos)} tipos de falla desde MySQL")
        return tipos
    except Exception as e:
        print(f"⚠️ Error cargando tipos_falla de MySQL: {e}")
        if conn:
            conn.close()
        # Fallback a valores por defecto
        return [
            {"nombre": "Mantenimiento", "color": "#FF9A00"},
            {"nombre": "Producción", "color": "#FF5252"},
            {"nombre": "Calidad", "color": "#4CAF50"},
            {"nombre": "Materiales", "color": "#2196F3"},
            {"nombre": "Ingeniería", "color": "#9C27B0"}
        ]
        
def guardar_tipos_falla(tipos, db_config):
    """Guarda la lista de tipos de falla en MySQL"""
    if db_config.get("tipo") != "mysql":
        print("❌ Error: guardar_tipos_falla solo funciona con MySQL")
        return False
    
    conn = obtener_conexion_mysql(db_config)
    if not conn:
        print("❌ No se pudo conectar a MySQL para guardar tipos de falla")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Limpiar tabla existente
        cursor.execute("DELETE FROM tipos_falla")
        
        # Insertar nuevos tipos
        for i, tipo in enumerate(tipos):
            cursor.execute(
                "INSERT INTO tipos_falla (nombre, color, orden) VALUES (%s, %s, %s)",
                (tipo["nombre"], tipo["color"], i)
            )
        
        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ Guardados {len(tipos)} tipos de falla en MySQL")
        return True
    except Exception as e:
        print(f"❌ Error guardando tipos_falla en MySQL: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False
    
# --- FUNCIONES PARA CONFIG_PROYECCION ---
def cargar_config_proyeccion(db_config):
    """Carga la configuración de proyección desde MySQL"""
    config = {
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
    
    if db_config.get("tipo") != "mysql":
        print("❌ Error: cargar_config_proyeccion solo funciona con MySQL")
        return config
    
    conn = obtener_conexion_mysql(db_config, timeout=5)
    if not conn:
        print("⚠️ No se pudo conectar a MySQL para cargar proyección, usando valores por defecto")
        return config
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM config_proyeccion WHERE id = 1")
        row = cursor.fetchone()
        if row:
            for key in config.keys():
                if key in row and row[key] is not None:
                    config[key] = row[key]
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"⚠️ Error cargando config_proyeccion de MySQL: {e}")
        if conn:
            conn.close()
    
    return config

def guardar_config_proyeccion(config, db_config):
    """Guarda la configuración de proyección en MySQL"""
    if db_config.get("tipo") != "mysql":
        print("❌ Error: guardar_config_proyeccion solo funciona con MySQL")
        return False
    
    conn = obtener_conexion_mysql(db_config)
    if not conn:
        print("❌ No se pudo conectar a MySQL para guardar proyección")
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE config_proyeccion SET
                pantalla_completa = %s,
                recordar_posicion = %s,
                x = %s,
                y = %s,
                ancho = %s,
                alto = %s,
                monitor = %s,
                color_fondo = %s,
                mostrar_contador = %s,
                color_texto = %s,
                color_acento = %s,
                color_exito = %s,
                mostrar_pendientes = %s
            WHERE id = 1
        ''', (
            config["pantalla_completa"],
            config["recordar_posicion"],
            config["x"],
            config["y"],
            config["ancho"],
            config["alto"],
            config["monitor"],
            config["color_fondo"],
            config["mostrar_contador"],
            config["color_texto"],
            config["color_acento"],
            config["color_exito"],
            config["mostrar_pendientes"]
        ))
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Configuración de proyección guardada en MySQL")
        return True
    except Exception as e:
        print(f"❌ Error guardando config_proyeccion en MySQL: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False
                
# --- FUNCIONES PARA CONFIG_CONTADOR ---
def cargar_config_contador(db_config):
    """Carga la configuración del contador de fallas desde MySQL"""
    config = {
        "ultimo_reset": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "consecutivo_actual": 0,
        "periodo_reset": "diario"
    }
    
    if db_config.get("tipo") != "mysql":
        print("❌ Error: cargar_config_contador solo funciona con MySQL")
        return config
    
    conn = obtener_conexion_mysql(db_config, timeout=5)
    if not conn:
        print("⚠️ No se pudo conectar a MySQL para cargar contador, usando valores por defecto")
        return config
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM config_contador WHERE id = 1")
        row = cursor.fetchone()
        if row:
            config["ultimo_reset"] = row["ultimo_reset"].strftime("%Y-%m-%d %H:%M:%S") if row["ultimo_reset"] else config["ultimo_reset"]
            config["consecutivo_actual"] = row["consecutivo_actual"] if row["consecutivo_actual"] is not None else 0
            config["periodo_reset"] = row["periodo_reset"] if row["periodo_reset"] else "diario"
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"⚠️ Error cargando config_contador de MySQL: {e}")
        if conn:
            conn.close()
    
    return config

def guardar_config_contador(config, db_config):
    """Guarda la configuración del contador en MySQL"""
    if db_config.get("tipo") != "mysql":
        print("❌ Error: guardar_config_contador solo funciona con MySQL")
        return False
    
    conn = obtener_conexion_mysql(db_config)
    if not conn:
        print("❌ No se pudo conectar a MySQL para guardar contador")
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE config_contador SET
                ultimo_reset = %s,
                consecutivo_actual = %s,
                periodo_reset = %s
            WHERE id = 1
        ''', (
            config["ultimo_reset"],
            config["consecutivo_actual"],
            config["periodo_reset"]
        ))
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Configuración de contador guardada en MySQL")
        return True
    except Exception as e:
        print(f"❌ Error guardando config_contador en MySQL: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False
                  
# --- FUNCIONES PARA CONFIG_LICENCIA ---
def cargar_config_licencia(db_config):
    """Carga la configuración de la licencia desde MySQL"""
    config = {
        "installation_id": hashlib.md5(str(os.environ.get('COMPUTERNAME', 'unknown')).encode()).hexdigest()[:12].upper(),
        "license_key": "",
        "license_type": "basic",
        "demo_used": False,
        "demo_start": "",
        "demo_expires": "",
        "max_fallas": 3,
        "max_maquinas": 5,
        "last_validation": "",
        "grace_period_start": "",
        "excel_exports_today": 0,
        "last_export_date": "",
        "expires_at": ""
    }
    
    if db_config.get("tipo") != "mysql":
        print("❌ Error: cargar_config_licencia solo funciona con MySQL")
        return config
    
    conn = obtener_conexion_mysql(db_config, timeout=5)
    if not conn:
        print("⚠️ No se pudo conectar a MySQL para cargar licencia, usando valores por defecto")
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
                    elif hasattr(row[key], 'strftime'):  # para date
                        config[key] = row[key].strftime("%Y-%m-%d")
                    else:
                        config[key] = row[key]
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"⚠️ Error cargando config_licencia de MySQL: {e}")
        if conn:
            conn.close()
    
    return config

def guardar_config_licencia(config, db_config):
    """Guarda la configuración de la licencia en MySQL"""
    print(f"💾 Guardando configuración de licencia: {config.get('license_type')}")
    
    if db_config.get("tipo") != "mysql":
        print("❌ Error: guardar_config_licencia solo funciona con MySQL")
        return False
    
    conn = obtener_conexion_mysql(db_config)
    if not conn:
        print("❌ No se pudo conectar a MySQL para guardar licencia")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Función auxiliar para convertir None a NULL para MySQL
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
        print(f"✅ Licencia guardada en MySQL: {config.get('license_type')}")
        return True
    except Exception as e:
        print(f"❌ Error guardando config_licencia en MySQL: {e}")
        if conn:
            conn.rollback()
            conn.close()
        import traceback
        traceback.print_exc()
        return False
    
# --- FUNCIONES PARA FALLAS ACTIVAS (versión simplificada sin migraciones) ---
def guardar_fallas_activas(fallas_en_memoria, db_config):
    """
    Sincroniza la tabla 'fallas_activas' con la lista en memoria.
    - Inserta las nuevas.
    - Actualiza las existentes.
    - Elimina las que ya no están en memoria.
    """
    if db_config.get("tipo") != "mysql":
        print("❌ Error: guardar_fallas_activas solo funciona con MySQL")
        return False
    
    conn = obtener_conexion_mysql(db_config)
    if not conn:
        print("❌ No se pudo conectar a MySQL para sincronizar fallas activas")
        return False
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 1. Obtener todas las fallas activas actuales en BD
        cursor.execute("SELECT numero_falla FROM fallas_activas")
        filas_bd = cursor.fetchall()
        numeros_en_bd = set(row['numero_falla'] for row in filas_bd)
        
        # 2. Obtener números de falla en memoria
        numeros_en_memoria = set(falla.get('numero_falla') for falla in fallas_en_memoria if falla.get('numero_falla'))
        
        # 3. Determinar qué insertar/actualizar y qué eliminar
        numeros_a_eliminar = numeros_en_bd - numeros_en_memoria
        
        # 4. Eliminar las que ya no están en memoria
        if numeros_a_eliminar:
            # Crear placeholders para la consulta IN
            placeholders = ','.join(['%s'] * len(numeros_a_eliminar))
            cursor.execute(f"DELETE FROM fallas_activas WHERE numero_falla IN ({placeholders})", tuple(numeros_a_eliminar))
            print(f"🗑️ Eliminadas {cursor.rowcount} fallas activas que ya no están en memoria")
        
        # 5. Insertar o actualizar las de memoria
        for falla in fallas_en_memoria:
            numero_falla = falla.get('numero_falla')
            if not numero_falla:
                print("⚠️ Falla sin número, ignorando")
                continue
            
            if numero_falla in numeros_en_bd:
                # Actualizar existente
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
                    numero_falla
                ))
            else:
                # Insertar nueva
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
                    numero_falla,
                    falla.get("estado", "activa"),
                    falla.get("nota_pendiente"),
                    falla.get("fecha_pendiente")
                ))
        
        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ Sincronización de fallas activas completada. {len(fallas_en_memoria)} en memoria.")
        return True
        
    except Exception as e:
        print(f"❌ Error en guardar_fallas_activas: {e}")
        if conn:
            conn.rollback()
            conn.close()
        import traceback
        traceback.print_exc()
        return False
       
# --- Funciones específicas para cada tipo de configuración ---
def cargar_fallas_activas(db_config):
    """Carga las fallas activas desde MySQL"""
    fallas = []
    
    if db_config.get("tipo") != "mysql":
        print("❌ Error: cargar_fallas_activas solo funciona con MySQL")
        return []
    
    conn = obtener_conexion_mysql(db_config, timeout=5)
    if not conn:
        print("⚠️ No se pudo conectar a MySQL para cargar fallas activas")
        return []
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT maquina, tipo, inicio, proceso, fin, numero_falla, estado, nota_pendiente, fecha_pendiente 
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
                "estado": row['estado'] if row['estado'] else "activa",
                "nota_pendiente": row['nota_pendiente'],
                "fecha_pendiente": row['fecha_pendiente'].strftime("%Y-%m-%d %H:%M:%S") if row['fecha_pendiente'] else None
            }
            fallas.append(falla)
        
        print(f"✅ Cargadas {len(fallas)} fallas activas desde MySQL")
    except Exception as e:
        print(f"❌ Error cargando fallas activas: {e}")
        if conn:
            conn.close()
    
    return fallas

# ============================================================================
# ========== FUNCIONES ORIGINALES (modificadas para usar BD) ==========
# ============================================================================

def cargar_config_db():
    """Carga la configuración de la base de datos desde JSON (solo para conectar a MySQL)"""
    config = DB_CONFIG_DEFAULT.copy()
    if os.path.exists(DB_CONFIG_FILE):
        try:
            with open(DB_CONFIG_FILE, 'r') as f:
                loaded_config = json.load(f)
                config.update(loaded_config)
        except:
            pass
    return config

def guardar_config_db(config):
    """Guarda la configuración de la base de datos en JSON"""
    with open(DB_CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def probar_conexion_mysql(config):
    """Prueba la conexión a MySQL con la configuración dada"""
    try:
        conn = mysql.connector.connect(
            host=config["host"],
            port=config["port"],
            user=config["usuario"],
            password=config["password"],
            database=config["base_datos"],
            connection_timeout=config["timeout"],
            ssl_disabled=not config["usar_ssl"],
            use_pure=True,
            autocommit=True,
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
        if conn.is_connected():
            print(f"✅ Conexión exitosa a MySQL {'con SSL' if config['usar_ssl'] else 'sin SSL'}")
            conn.close()
            return True, f"Conexión exitosa {'con SSL' if config['usar_ssl'] else 'sin SSL'}"
    except Error as e:
        print(f"❌ Error MySQL: {e}")
        if config["usar_ssl"]:
            try:
                conn = mysql.connector.connect(
                    host=config["host"],
                    port=config["port"],
                    user=config["usuario"],
                    password=config["password"],
                    database=config["base_datos"],
                    connection_timeout=config["timeout"],
                    ssl_disabled=True,
                    use_pure=True
                )
                if conn.is_connected():
                    conn.close()
                    return True, "Conexión exitosa (sin SSL - respaldo)"
            except:
                pass
        return False, str(e)
    return False, "No se pudo conectar"

def inicializar_db_mysql(config):
    """Inicializa la base de datos MySQL creando las tablas si no existen"""
    try:
        conn = mysql.connector.connect(
            host=config["host"],
            port=config["port"],
            user=config["usuario"],
            password=config["password"],
            connection_timeout=config["timeout"],
            ssl_disabled=not config["usar_ssl"]
        )
        cursor = conn.cursor()

        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config['base_datos']}")
        cursor.execute(f"USE {config['base_datos']}")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fallas (
                id INT AUTO_INCREMENT PRIMARY KEY,
                maquina VARCHAR(50),
                tipo VARCHAR(100),
                inicio DATETIME,
                proceso DATETIME,
                fin DATETIME,
                t_inicio_proceso VARCHAR(50),
                t_proceso_fin VARCHAR(50),
                t_total VARCHAR(50),
                numero_falla INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()
        return True, "Base de datos inicializada correctamente"
    except Error as e:
        return False, str(e)
   
def guardar_falla(alerta, db_config=None):
    """
    Guarda una falla en la base de datos MySQL.
    - Si la falla tiene estado 'resuelta', se guarda en el historial ('fallas') 
      y se elimina de activas.
    - En cualquier otro caso, se guarda/actualiza en 'fallas_activas'.
    """
    if db_config is None:
        db_config = cargar_config_db()
    
    if db_config.get("tipo") != "mysql":
        print("❌ Error: guardar_falla solo funciona con MySQL")
        return False
    
    # Verificar si la falla está resuelta (tiene fin)
    if alerta.get("estado") == "resuelta" or alerta.get("fin"):
        # Guardar en historial
        exito_historial = guardar_falla_en_historial(alerta, db_config)
        if exito_historial:
            # Si se guardó bien en historial, eliminar de activas
            eliminar_falla_activa(alerta.get("numero_falla"), db_config)
            return True
        else:
            return False
    else:
        # Guardar o actualizar en activas
        return guardar_falla_activa(alerta, db_config)
    

# ============================================================================
# ========== FUNCIONES DE FALLAS (FUERA DE LA CLASE) ==========
# ============================================================================

def guardar_falla_en_historial(alerta, db_config):
    """
    Guarda una falla FINALIZADA en la tabla de historial 'fallas'.
    Se llama cuando una falla pasa a estado 'resuelta'.
    """
    if db_config.get("tipo") != "mysql":
        print("❌ Error: guardar_falla_en_historial solo funciona con MySQL")
        return False
    
    conn = obtener_conexion_mysql(db_config)
    if not conn:
        print("❌ No se pudo conectar a MySQL para guardar en historial")
        return False
    
    try:
        cursor = conn.cursor()
        
        formato = "%Y-%m-%d %H:%M:%S"
        t_inicio_proceso = None
        t_proceso_fin = None
        t_total = None
        
        inicio = alerta.get("inicio")
        proceso = alerta.get("proceso")
        fin = alerta.get("fin")
        
        # Calcular tiempos si es posible
        if inicio and proceso and fin:
            try:
                dt_inicio = datetime.strptime(inicio, formato)
                dt_proceso = datetime.strptime(proceso, formato)
                dt_fin = datetime.strptime(fin, formato)
                
                # Tiempo de inicio a proceso
                diff_inicio_proceso = dt_proceso - dt_inicio
                horas = diff_inicio_proceso.seconds // 3600
                minutos = (diff_inicio_proceso.seconds % 3600) // 60
                segundos = diff_inicio_proceso.seconds % 60
                t_inicio_proceso = f"{horas:02d}:{minutos:02d}:{segundos:02d}"
                
                # Tiempo de proceso a fin
                diff_proceso_fin = dt_fin - dt_proceso
                horas = diff_proceso_fin.seconds // 3600
                minutos = (diff_proceso_fin.seconds % 3600) // 60
                segundos = diff_proceso_fin.seconds % 60
                t_proceso_fin = f"{horas:02d}:{minutos:02d}:{segundos:02d}"
                
                # Tiempo total
                diff_total = dt_fin - dt_inicio
                horas = diff_total.seconds // 3600
                minutos = (diff_total.seconds % 3600) // 60
                segundos = diff_total.seconds % 60
                t_total = f"{horas:02d}:{minutos:02d}:{segundos:02d}"
            except Exception as e:
                print(f"⚠️ Error calculando tiempos: {e}")
        
        elif inicio and fin:
            try:
                dt_inicio = datetime.strptime(inicio, formato)
                dt_fin = datetime.strptime(fin, formato)
                diff_total = dt_fin - dt_inicio
                horas = diff_total.seconds // 3600
                minutos = (diff_total.seconds % 3600) // 60
                segundos = diff_total.seconds % 60
                t_total = f"{horas:02d}:{minutos:02d}:{segundos:02d}"
            except Exception as e:
                print(f"⚠️ Error calculando tiempo total: {e}")
        
        # Insertar en historial
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
            "resuelta",  # Forzar estado resuelta
            alerta.get("nota_pendiente"),
            alerta.get("fecha_pendiente")
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ Falla #{alerta.get('numero_falla', '')} guardada en historial MySQL")
        return True
        
    except Exception as e:
        print(f"❌ Error en guardar_falla_en_historial: {e}")
        if conn:
            conn.rollback()
            conn.close()
        import traceback
        traceback.print_exc()
        return False


def guardar_falla_activa(alerta, db_config):
    """
    Guarda o actualiza una falla en la tabla 'fallas_activas'.
    - Si la falla ya existe (por número_falla), la actualiza.
    - Si no existe, la inserta.
    """
    if db_config.get("tipo") != "mysql":
        print("❌ Error: guardar_falla_activa solo funciona con MySQL")
        return False
    
    conn = obtener_conexion_mysql(db_config)
    if not conn:
        print("❌ No se pudo conectar a MySQL para guardar falla activa")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Verificar si ya existe por número de falla
        cursor.execute("SELECT id FROM fallas_activas WHERE numero_falla = %s", (alerta.get("numero_falla"),))
        existe = cursor.fetchone()
        
        if existe:
            # UPDATE
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
            print(f"🔄 Falla activa #{alerta.get('numero_falla')} actualizada")
        else:
            # INSERT
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
            print(f"✅ Nueva falla activa #{alerta.get('numero_falla')} insertada")
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error en guardar_falla_activa: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


def eliminar_falla_activa(numero_falla, db_config):
    """
    Elimina una falla de la tabla 'fallas_activas' por su número de falla.
    """
    if db_config.get("tipo") != "mysql":
        print("❌ Error: eliminar_falla_activa solo funciona con MySQL")
        return False
    
    conn = obtener_conexion_mysql(db_config)
    if not conn:
        print("❌ No se pudo conectar a MySQL para eliminar falla activa")
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM fallas_activas WHERE numero_falla = %s", (numero_falla,))
        eliminadas = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        if eliminadas > 0:
            print(f"✅ Falla activa #{numero_falla} eliminada")
        else:
            print(f"⚠️ No se encontró falla activa #{numero_falla} para eliminar")
        
        return True
    except Exception as e:
        print(f"❌ Error en eliminar_falla_activa: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False
      
# ============================================================================
# ========== FUNCIONES DE LICENCIAMIENTO (sin cambios) ==========
# ============================================================================

def validar_licencia_online(license_key, installation_id):
    """Valida la licencia contra la base de datos central - VERSION MEJORADA"""
    print(f"🔍 Intentando validar licencia: {license_key}")
    
    try:
        # Probar primero con SSL habilitado
        try:
            conn = mysql.connector.connect(
                host=LICENSE_DB_CONFIG["host"],
                port=LICENSE_DB_CONFIG["port"],
                user=LICENSE_DB_CONFIG["usuario"],
                password=LICENSE_DB_CONFIG["password"],
                database=LICENSE_DB_CONFIG["base_datos"],
                connection_timeout=LICENSE_DB_CONFIG["timeout"],
                ssl_disabled=False,  # Con SSL primero
                use_pure=True,
                allow_local_infile=False
            )
            print("✅ Conexión SSL exitosa")
            
        except mysql.connector.Error as e:
            print(f"⚠️ SSL falló, intentando sin SSL: {e}")
            # Si SSL falla, intentar sin SSL
            conn = mysql.connector.connect(
                host=LICENSE_DB_CONFIG["host"],
                port=LICENSE_DB_CONFIG["port"],
                user=LICENSE_DB_CONFIG["usuario"],
                password=LICENSE_DB_CONFIG["password"],
                database=LICENSE_DB_CONFIG["base_datos"],
                connection_timeout=LICENSE_DB_CONFIG["timeout"],
                ssl_disabled=True,  # Sin SSL
                use_pure=True,
                allow_local_infile=False
            )
            print("✅ Conexión sin SSL exitosa")
        
        cursor = conn.cursor(dictionary=True)

        # Buscar licencia
        cursor.execute("""
            SELECT * FROM licencias
            WHERE license_key = %s AND is_active = 1
        """, (license_key,))
        
        licencia = cursor.fetchone()
        
        if not licencia:
            conn.close()
            print("❌ Licencia no encontrada en BD")
            return False, "Licencia no válida o inactiva"
            
        # Verificar si la licencia ya está asignada
        if licencia['installation_id'] and licencia['installation_id'] != installation_id:
            print(f"⚠️ Licencia ya asignada a otra instalación: {licencia['installation_id']}")
            
            # Opcional: preguntar si quiere reasignar
            # Por ahora, devolvemos error
            conn.close()
            return False, f"Esta licencia ya está asignada a otra instalación"
        
        # Verificar expiración
        hoy = datetime.now().date()
        expiracion = licencia['expires_at']
        
        if isinstance(expiracion, str):
            expiracion = datetime.strptime(expiracion, "%Y-%m-%d").date()
            
        if hoy > expiracion:
            conn.close()
            return False, f"Licencia expirada el {expiracion}"
            
        # Actualizar la licencia con este installation_id
        cursor.execute("""
            UPDATE licencias SET 
                installation_id = %s,
                last_validated = NOW()
            WHERE id = %s
        """, (installation_id, licencia['id']))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Licencia validada exitosamente: {licencia['license_type']}")
        
        return True, {
            'license_type': licencia['license_type'],
            'max_fallas': licencia['max_fallas'],
            'max_maquinas': licencia['max_maquinas'],
            'expires_at': expiracion.strftime("%Y-%m-%d") if hasattr(expiracion, 'strftime') else str(expiracion)
        }

    except mysql.connector.Error as e:
        error_msg = str(e)
        print(f"❌ Error MySQL validando licencia: {error_msg}")
        
        # Errores comunes y mensajes amigables
        if "2003" in error_msg:
            return False, "No se pudo conectar al servidor de licencias. Verifica tu conexión a internet."
        elif "1045" in error_msg:
            return False, "Error de autenticación en servidor de licencias."
        elif "2005" in error_msg:
            return False, "No se pudo resolver el host del servidor de licencias."
        else:
            return False, f"Error de conexión: {error_msg}"
            
    except Exception as e:
        print(f"❌ Error general validando licencia: {e}")
        import traceback
        traceback.print_exc()
        return False, f"Error inesperado: {str(e)}"
    
def iniciar_demo(installation_id):
    """Inicia un periodo de demo - VERSIÓN CORREGIDA con todas las columnas"""
    print(f"🎁 Intentando iniciar demo para: {installation_id}")
    
    try:
        # Obtener IP (opcional)
        ip_address = "0.0.0.0"
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip_address = s.getsockname()[0]
            s.close()
        except:
            pass

        # Probar conexión
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
        
        demo_existente = cursor.fetchone()

        if demo_existente:
            conn.close()
            return False, "Ya has utilizado el periodo de demo"

        # Fechas del demo
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fecha_expiracion = (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d")

        # ✅ INSERT con TODAS las columnas
        cursor.execute("""
            INSERT INTO demo_installations 
            (installation_id, ip_address, started_at, expires_at, is_expired, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            installation_id, 
            ip_address, 
            fecha_actual, 
            fecha_expiracion,
            0,  # is_expired = False
            fecha_actual  # created_at
        ))

        conn.commit()
        conn.close()

        print(f"✅ Demo iniciado correctamente, expira: {fecha_expiracion}")
        return True, fecha_expiracion

    except mysql.connector.Error as e:
        error_msg = str(e)
        print(f"❌ Error MySQL: {error_msg}")
        
        # Si el error es por número de columnas, mostrar mensaje específico
        if "Column count doesn't match" in error_msg:
            return False, "Error: La estructura de la tabla ha cambiado. Contacta al soporte."
        else:
            return False, f"Error de conexión: {error_msg}"
            
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()
        return False, f"Error inesperado: {str(e)}"

def verificar_estado_licencia():
    """Verifica el estado de la licencia - AHORA CORREGIDA para respetar licencias de pago"""
    print("🔍 Verificando estado de licencia...")

   
    temp_db_config = {"tipo": "mysql"}
    config = cargar_config_licencia(self.db_config)

    print(f"📄 Configuración cargada: {config}")

    hoy = datetime.now()

    # --- LÓGICA CORREGIDA PARA LICENCIAS DE PAGO ---
    if config['license_key'] and config['license_type'] in ['pro', 'mid']:
        # Es una licencia de pago. No necesitamos validación online constante.
        # Solo verificamos que no haya expirado (si tenemos fecha de expiración)
        if config.get('expires_at'): # Asegúrate de que 'expires_at' se guarde al validar
            try:
                expiracion = datetime.strptime(config['expires_at'], "%Y-%m-%d")
                if hoy.date() > expiracion.date():
                    print("❌ Licencia expirada")
                    # Podrías ponerla en modo de gracia aquí si lo deseas
                    return False, "Licencia expirada"
            except:
                pass # Si no hay fecha, asumimos que es válida

        # Si llegamos aquí, la licencia es válida
        print(f"✅ Licencia {config['license_type'].upper()} válida (offline)")
        return True, config

    # --- LÓGICA PARA DEMO ---
    elif config.get('demo_used') and config.get('demo_expires'):
        try:
            demo_expira = datetime.strptime(config['demo_expires'], "%Y-%m-%d")
            if hoy.date() <= demo_expira.date():
                print("✅ Demo activa")
                return True, config
            else:
                print("❌ Demo expirada")
                return False, "Periodo de demo expirado"
        except:
            print("⚠️ Error al validar fecha de demo, asumiendo demo inválida")
            return False, "Error en fecha de demo"

    # --- MODO BÁSICO POR DEFECTO (solo si no hay nada) ---
    else:
        # Si no hay licencia ni demo, pero tenemos datos en la BD, es un error.
        # Esto puede pasar si la tabla de licencia está corrupta.
        if config['installation_id'] and not config['license_key'] and not config.get('demo_used'):
            print("ℹ️ No hay licencia activa, iniciando en modo básico")
        else:
            print("ℹ️ Modo básico activado (por defecto)")
        return True, config
    
def verificar_limite_maquinas(config, maquina):
    """Verifica si la máquina está dentro del límite permitido"""
    if config['license_type'] == 'pro':
        return True

    max_maquinas = config.get('max_maquinas', 5)
    try:
        num_maquina = int(maquina)
        if num_maquina > max_maquinas:
            return False
    except:
        pass
    return True

def verificar_limite_excel_exports(config):
    """Verifica si se puede exportar Excel según límite diario"""
    if config['license_type'] == 'pro':
        return True

    hoy = datetime.now().strftime("%Y-%m-%d")
    if config['last_export_date'] != hoy:
        config['excel_exports_today'] = 0
        config['last_export_date'] = hoy

    if config['license_type'] == 'mid' and config['excel_exports_today'] >= 1:
        return False

    return True

def registrar_export_excel():
    """Registra una exportación de Excel"""
    db_config = cargar_config_db()
    config = cargar_config_licencia(db_config)
    hoy = datetime.now().strftime("%Y-%m-%d")

    if config['last_export_date'] != hoy:
        config['excel_exports_today'] = 0
        config['last_export_date'] = hoy

    config['excel_exports_today'] += 1
    guardar_config_licencia(config, db_config)

# ============================================================================
# ========== CLASES DE LICENCIA (sin cambios) ==========
# ============================================================================

class MenuLicencia:
    """Menú para gestionar la licencia desde la aplicación"""

    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.config = app.licencia_config.copy()

        self.ventana = tk.Toplevel(parent)
        self.ventana.title("Gestión de Licencia")
        self.ventana.geometry("550x700")
        self.ventana.configure(bg=COLORES["fondo"])
        self.ventana.resizable(False, False)
        self.ventana.transient(parent)
        self.ventana.grab_set()

        self.ventana.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (550 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (700 // 2)
        self.ventana.geometry(f"+{x}+{y}")

        self.setup_ui()

    def setup_ui(self):
        # Título
        tk.Label(self.ventana,
                text="🔐 Gestión de Licencia Andon",
                bg=COLORES["fondo"],
                fg=COLORES["texto"],
                font=("Segoe UI", 18, "bold")).pack(pady=20)

        # Frame principal con scroll
        container = tk.Frame(self.ventana, bg=COLORES["fondo"])
        container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        canvas = tk.Canvas(container, bg=COLORES["fondo"], highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)

        scrollable_frame = tk.Frame(canvas, bg=COLORES["fondo"])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=canvas.winfo_width())

        def configure_frame_width(event):
            canvas.itemconfig(1, width=event.width)

        canvas.bind('<Configure>', configure_frame_width)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # ===== ID DE INSTALACIÓN =====
        id_card = tk.Frame(scrollable_frame, bg=COLORES["card"], relief="flat", bd=1)
        id_card.pack(fill="x", pady=(0, 15))

        tk.Label(id_card,
                text="🆔 ID de Instalación",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15, pady=(15, 5))

        id_frame = tk.Frame(id_card, bg=COLORES["card"])
        id_frame.pack(fill="x", padx=15, pady=(0, 15))

        id_label = tk.Label(id_frame,
                           text=self.config['installation_id'],
                           bg=COLORES["fondo"],
                           fg=COLORES["accento"],
                           font=("Consolas", 12, "bold"),
                           padx=10,
                           pady=5)
        id_label.pack(side="left")

        tk.Button(id_frame,
                 text="📋 Copiar",
                 bg=COLORES["card"],
                 fg=COLORES["texto"],
                 font=("Segoe UI", 8),
                 relief="flat",
                 padx=8,
                 pady=2,
                 cursor="hand2",
                 command=lambda: self.copiar_al_portapapeles(self.config['installation_id'])).pack(side="left", padx=5)

        # ===== ESTADO ACTUAL =====
        estado_card = tk.Frame(scrollable_frame, bg=COLORES["card"], relief="flat", bd=1)
        estado_card.pack(fill="x", pady=(0, 15))

        tk.Label(estado_card,
                text="📊 Estado Actual",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15, pady=(15, 10))

        tipo_frame = tk.Frame(estado_card, bg=COLORES["card"])
        tipo_frame.pack(fill="x", padx=15, pady=5)

        tk.Label(tipo_frame,
                text="Tipo:",
                bg=COLORES["card"],
                fg=COLORES["texto_secundario"],
                width=15,
                anchor="w").pack(side="left")

        tipo_text = self.config.get('license_type', 'basic').upper()
        if tipo_text == 'PRO':
            color_tipo = "#4CAF50"
            descripcion = "✓ Todas las funciones"
        elif tipo_text == 'MID':
            color_tipo = "#FFC107"
            descripcion = "✓ Funciones intermedias"
        elif tipo_text == 'DEMO':
            color_tipo = "#9C27B0"
            descripcion = "✓ Versión de prueba (PRO)"
            tipo_text = "DEMO (PRO)"
        else:
            color_tipo = "#FF5252"
            descripcion = "✗ Funciones básicas"

        tk.Label(tipo_frame,
                text=tipo_text,
                bg=color_tipo,
                fg="white" if tipo_text not in ['MID', 'DEMO (PRO)'] else "black",
                font=("Segoe UI", 10, "bold"),
                padx=10,
                pady=2).pack(side="left", padx=(0, 10))

        tk.Label(tipo_frame,
                text=descripcion,
                bg=COLORES["card"],
                fg=COLORES["texto_secundario"],
                font=("Segoe UI", 9, "italic")).pack(side="left")

        limites_frame = tk.Frame(estado_card, bg=COLORES["card"])
        limites_frame.pack(fill="x", padx=15, pady=5)

        tk.Label(limites_frame,
                text="Tipos de falla:",
                bg=COLORES["card"],
                fg=COLORES["texto_secundario"],
                width=20,
                anchor="w").pack(side="left")

        tk.Label(limites_frame,
                text=str(self.config.get('max_fallas', 3)),
                bg=COLORES["card"],
                fg=COLORES["success"],
                font=("Segoe UI", 11, "bold")).pack(side="left")

        limites2_frame = tk.Frame(estado_card, bg=COLORES["card"])
        limites2_frame.pack(fill="x", padx=15, pady=5)

        tk.Label(limites2_frame,
                text="Límite máquinas:",
                bg=COLORES["card"],
                fg=COLORES["texto_secundario"],
                width=20,
                anchor="w").pack(side="left")

        tk.Label(limites2_frame,
                text=str(self.config.get('max_maquinas', 5)),
                bg=COLORES["card"],
                fg=COLORES["success"],
                font=("Segoe UI", 11, "bold")).pack(side="left")

        # ===== FECHAS IMPORTANTES =====
        fechas_card = tk.Frame(scrollable_frame, bg=COLORES["card"], relief="flat", bd=1)
        fechas_card.pack(fill="x", pady=(0, 15))

        tk.Label(fechas_card,
                text="📅 Fechas Importantes",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15, pady=(15, 10))

        if self.config.get('demo_expires'):
            demo_frame = tk.Frame(fechas_card, bg=COLORES["card"])
            demo_frame.pack(fill="x", padx=15, pady=5)

            tk.Label(demo_frame,
                    text="Demo expira:",
                    bg=COLORES["card"],
                    fg=COLORES["texto_secundario"],
                    width=15,
                    anchor="w").pack(side="left")

            try:
                fecha_demo = datetime.strptime(self.config['demo_expires'], "%Y-%m-%d")
                dias_restantes = (fecha_demo - datetime.now().date()).days

                color_dias = "#4CAF50" if dias_restantes > 7 else "#FFC107" if dias_restantes > 0 else "#FF5252"

                tk.Label(demo_frame,
                        text=f"{self.config['demo_expires']} ({dias_restantes} días restantes)",
                        bg=COLORES["card"],
                        fg=color_dias,
                        font=("Segoe UI", 10, "bold")).pack(side="left")
            except:
                tk.Label(demo_frame,
                        text=self.config['demo_expires'],
                        bg=COLORES["card"],
                        fg=COLORES["texto"],
                        font=("Segoe UI", 10)).pack(side="left")
        else:
            demo_frame = tk.Frame(fechas_card, bg=COLORES["card"])
            demo_frame.pack(fill="x", padx=15, pady=5)

            tk.Label(demo_frame,
                    text="Demo:",
                    bg=COLORES["card"],
                    fg=COLORES["texto_secundario"],
                    width=15,
                    anchor="w").pack(side="left")

            tk.Label(demo_frame,
                    text="No activada",
                    bg=COLORES["card"],
                    fg=COLORES["texto_secundario"],
                    font=("Segoe UI", 10, "italic")).pack(side="left")

        if self.config.get('license_key') and self.config.get('license_type') != 'demo':
            licencia_frame = tk.Frame(fechas_card, bg=COLORES["card"])
            licencia_frame.pack(fill="x", padx=15, pady=5)

            tk.Label(licencia_frame,
                    text="Licencia válida:",
                    bg=COLORES["card"],
                    fg=COLORES["texto_secundario"],
                    width=15,
                    anchor="w").pack(side="left")

            tk.Label(licencia_frame,
                    text="✓ Activa",
                    bg=COLORES["card"],
                    fg=COLORES["success"],
                    font=("Segoe UI", 10, "bold")).pack(side="left")

        if self.config.get('last_validation'):
            valid_frame = tk.Frame(fechas_card, bg=COLORES["card"])
            valid_frame.pack(fill="x", padx=15, pady=5)

            tk.Label(valid_frame,
                    text="Última validación:",
                    bg=COLORES["card"],
                    fg=COLORES["texto_secundario"],
                    width=15,
                    anchor="w").pack(side="left")

            try:
                fecha_valid = datetime.strptime(self.config['last_validation'], "%Y-%m-%d %H:%M:%S")
                tk.Label(valid_frame,
                        text=fecha_valid.strftime("%d/%m/%Y %H:%M"),
                        bg=COLORES["card"],
                        fg=COLORES["texto"],
                        font=("Segoe UI", 10)).pack(side="left")
            except:
                tk.Label(valid_frame,
                        text=self.config['last_validation'],
                        bg=COLORES["card"],
                        fg=COLORES["texto"],
                        font=("Segoe UI", 10)).pack(side="left")

        # ===== CAMBIAR LICENCIA =====
        cambiar_card = tk.Frame(scrollable_frame, bg=COLORES["card"], relief="flat", bd=1)
        cambiar_card.pack(fill="x", pady=(0, 15))

        tk.Label(cambiar_card,
                text="🔄 Cambiar Licencia",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15, pady=(15, 10))

        btn_frame = tk.Frame(cambiar_card, bg=COLORES["card"])
        btn_frame.pack(fill="x", padx=15, pady=(0, 15))

        tk.Button(btn_frame,
                 text="🔑 Activar Nueva Licencia",
                 bg=COLORES["success"],
                 fg=COLORES["texto"],
                 font=("Segoe UI", 11, "bold"),
                 relief="flat",
                 padx=20,
                 pady=8,
                 cursor="hand2",
                 command=self.mostrar_activacion).pack(fill="x", pady=5)

        tk.Button(btn_frame,
                 text="🎁 Iniciar Demo (15 días)",
                 bg=COLORES["warning"],
                 fg=COLORES["negro"],
                 font=("Segoe UI", 11),
                 relief="flat",
                 padx=20,
                 pady=8,
                 cursor="hand2",
                 command=self.iniciar_demo_desde_menu).pack(fill="x", pady=5)

        tk.Button(btn_frame,
                 text="🔄 Desactivar Licencia Actual",
                 bg=COLORES["danger"],
                 fg=COLORES["texto"],
                 font=("Segoe UI", 11),
                 relief="flat",
                 padx=20,
                 pady=8,
                 cursor="hand2",
                 command=self.desactivar_licencia).pack(fill="x", pady=5)

        # ===== INFORMACIÓN DE LICENCIAS =====
        info_card = tk.Frame(scrollable_frame, bg=COLORES["card"], relief="flat", bd=1)
        info_card.pack(fill="x", pady=(0, 15))

        tk.Label(info_card,
                text="ℹ️ Información de Licencias",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15, pady=(15, 10))

        info_text = tk.Text(info_card,
                          height=8,
                          width=50,
                          bg="#2d3047",
                          fg=COLORES["texto"],
                          font=("Segoe UI", 9),
                          relief="flat",
                          wrap="word")
        info_text.pack(fill="x", padx=15, pady=(0, 15))
        info_text.insert("1.0", self.obtext_info_licencias())
        info_text.config(state="disabled")

        button_frame = tk.Frame(scrollable_frame, bg=COLORES["fondo"])
        button_frame.pack(fill="x", pady=10)

        tk.Button(button_frame,
                 text="🔄 Validar Ahora",
                 bg=COLORES["warning"],
                 fg=COLORES["negro"],
                 font=("Segoe UI", 11),
                 relief="flat",
                 padx=20,
                 pady=10,
                 cursor="hand2",
                 command=self.validar_ahora).pack(side="left", padx=5)

        tk.Button(button_frame,
                 text="❌ Cerrar",
                 bg=COLORES["danger"],
                 fg=COLORES["texto"],
                 font=("Segoe UI", 11),
                 relief="flat",
                 padx=20,
                 pady=10,
                 cursor="hand2",
                 command=self.ventana.destroy).pack(side="right", padx=5)

        self.ventana.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

    def copiar_al_portapapeles(self, texto):
        self.ventana.clipboard_clear()
        self.ventana.clipboard_append(texto)
        messagebox.showinfo("✅ Copiado", "ID de instalación copiado al portapapeles", parent=self.ventana)

    def obtext_info_licencias(self):
        return """📋 TIPOS DE LICENCIA:

🔴 BASIC (Gratuita):
  • 3 TIPOS de falla máximo
  • 5 máquinas máximo
  • MySQL
  • Sin gráficas en Excel

🟡 MID ($):
  • 4 TIPOS de falla máximo
  • 15 máquinas máximo
  • 1 exportación Excel/día con gráficas
  • Configuración avanzada

🟢 PRO ($$):
  • 5+ TIPOS de falla
  • 200+ máquinas
  • MySQL 
  • Exportación ilimitada
  • Código ESP32
  • Todas las funciones

🎁 DEMO (15 días):
  • Acceso completo PRO
  • 15 días de prueba"""

    def mostrar_activacion(self):
        ventana = VentanaActivacion(self.ventana, self.config, self.app.db_config)
        self.ventana.wait_window(ventana.ventana)
        if ventana.resultado:
            self.config = ventana.resultado
            self.app.licencia_config = ventana.resultado
            self.app.aplicar_limites_licencia()
            messagebox.showinfo("✅ Licencia Actualizada",
                            "La licencia ha sido actualizada correctamente.\n"
                            "Los cambios se aplicarán inmediatamente.",
                            parent=self.ventana)
            self.ventana.destroy()

    def iniciar_demo_desde_menu(self):
        if self.config.get('demo_used'):
            messagebox.showerror("Error", "Ya has utilizado el periodo de demo", parent=self.ventana)
            return

        respuesta = messagebox.askyesno(
            "Confirmar Demo",
            "¿Estás seguro de iniciar el periodo de demo de 15 días?\n\n"
            "⚠️ ADVERTENCIA: Esta acción no se puede deshacer.\n"
            "Una vez iniciado, no podrás volver a usar la demo.",
            parent=self.ventana
        )

        if not respuesta:
            return

        exito, info = iniciar_demo(self.config['installation_id'])

        if exito:
            self.config['demo_used'] = True
            self.config['demo_start'] = datetime.now().strftime("%Y-%m-%d")
            self.config['demo_expires'] = info
            self.config['license_type'] = 'demo'
            guardar_config_licencia(self.config, self.app.db_config)

            self.app.licencia_config = self.config
            self.app.aplicar_limites_licencia()

            messagebox.showinfo("🎁 Demo Activado",
                              f"Periodo de demo de 15 días activado\n"
                              f"Válido hasta: {info}\n\n"
                              f"Tendrás acceso a la versión PRO durante este periodo.",
                              parent=self.ventana)
            self.ventana.destroy()
        else:
            messagebox.showerror("❌ Error", f"No se pudo iniciar demo:\n{info}", parent=self.ventana)

    def desactivar_licencia(self):
        if not self.config.get('license_key') and not self.config.get('demo_used'):
            messagebox.showinfo("Información", "No hay una licencia activa para desactivar.", parent=self.ventana)
            return

        respuesta = messagebox.askyesno(
            "⚠️ Confirmar Desactivación",
            "¿Estás seguro de desactivar la licencia actual?\n\n"
            "Esto eliminará la licencia y volverás al modo básico.\n"
            "Tendrás que volver a activar una licencia para usar funciones avanzadas.",
            parent=self.ventana
        )

        if respuesta:
            self.config['license_key'] = ""
            self.config['license_type'] = "basic"
            self.config['max_fallas'] = 3
            self.config['max_maquinas'] = 5
            self.config['last_validation'] = ""
            self.config['demo_used'] = False
            self.config['demo_expires'] = ""
            guardar_config_licencia(self.config, self.app.db_config)

            self.app.licencia_config = self.config
            self.app.aplicar_limites_licencia()

            messagebox.showinfo("✅ Licencia Desactivada",
                              "La licencia ha sido desactivada.\n"
                              "Ahora estás usando el modo básico.",
                              parent=self.ventana)
            self.ventana.destroy()

    def validar_ahora(self):
        valido, info = verificar_estado_licencia()
        if valido:
            self.config = cargar_config_licencia(self.app.db_config)
            self.app.licencia_config = self.config
            self.app.aplicar_limites_licencia()

            messagebox.showinfo("✅ Licencia Válida",
                              f"Tu licencia está activa.\n"
                              f"Tipo: {self.config.get('license_type', 'desconocido').upper()}\n"
                              f"Tipos de falla: {self.config.get('max_fallas', 3)}\n"
                              f"Límite máquinas: {self.config.get('max_maquinas', 5)}",
                              parent=self.ventana)
            self.ventana.destroy()
        else:
            messagebox.showwarning("⚠️ Atención",
                                 info if isinstance(info, str) else "Licencia no válida",
                                 parent=self.ventana)

class VentanaActivacion:
    def __init__(self, parent, config_licencia, db_config):
        self.parent = parent
        self.config = config_licencia
        self.db_config = db_config
        self.resultado = None

        self.ventana = tk.Toplevel(parent)
        self.ventana.title("Activación de Licencia")
        self.ventana.geometry("500x400")
        self.ventana.configure(bg=COLORES["fondo"])
        self.ventana.resizable(False, False)
        self.ventana.transient(parent)
        self.ventana.grab_set()

        self.ventana.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (500 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (400 // 2)
        self.ventana.geometry(f"+{x}+{y}")

        self.setup_ui()

    def setup_ui(self):
        tk.Label(self.ventana,
                text="🔐 Activación de Licencia Andon",
                bg=COLORES["fondo"],
                fg=COLORES["texto"],
                font=("Segoe UI", 16, "bold")).pack(pady=20)

        tk.Label(self.ventana,
                text=f"ID de Instalación:",
                bg=COLORES["fondo"],
                fg=COLORES["texto_secundario"],
                font=("Segoe UI", 10)).pack(pady=(10, 0))

        tk.Label(self.ventana,
                text=self.config['installation_id'],
                bg=COLORES["card"],
                fg=COLORES["accento"],
                font=("Segoe UI", 10, "bold"),
                padx=20,
                pady=10).pack()

        tk.Label(self.ventana,
                text="Licencia Demo de 15 días disponible",
                bg=COLORES["fondo"],
                fg=COLORES["warning"],
                font=("Segoe UI", 11, "bold")).pack(pady=10)

        tk.Frame(self.ventana, bg=COLORES["texto_secundario"], height=1).pack(fill="x", padx=20, pady=10)

        tk.Label(self.ventana,
                text="Ingresa tu clave de licencia:",
                bg=COLORES["fondo"],
                fg=COLORES["texto"],
                font=("Segoe UI", 11)).pack(pady=(10, 5))

        self.entry_licencia = tk.Entry(self.ventana,
                                      width=30,
                                      bg=COLORES.get("superficie3", "#2d3047"),
                                      fg=COLORES["texto"],
                                      font=("Segoe UI", 11),
                                      relief="flat")
        self.entry_licencia.pack(pady=10)

        button_frame = tk.Frame(self.ventana, bg=COLORES["fondo"])
        button_frame.pack(pady=20)

        tk.Button(button_frame,
                 text="✅ Activar Licencia",
                 bg=COLORES["success"],
                 fg=COLORES["texto"],
                 font=("Segoe UI", 11, "bold"),
                 relief="flat",
                 padx=20,
                 pady=10,
                 cursor="hand2",
                 command=self.activar_licencia).pack(side="left", padx=5)

        tk.Button(button_frame,
                 text="🎁 Iniciar Demo",
                 bg=COLORES["warning"],
                 fg=COLORES["negro"],
                 font=("Segoe UI", 11, "bold"),
                 relief="flat",
                 padx=20,
                 pady=10,
                 cursor="hand2",
                 command=self.iniciar_demo).pack(side="left", padx=5)

    def activar_licencia(self):
        license_key = self.entry_licencia.get().strip()
        if not license_key:
            messagebox.showerror("Error", "Ingresa una clave de licencia", parent=self.ventana)
            return

        valido, info = validar_licencia_online(license_key, self.config['installation_id'])

        if valido:
            self.config['license_key'] = license_key
            self.config['license_type'] = info['license_type']
            self.config['max_fallas'] = info['max_fallas']
            self.config['max_maquinas'] = info['max_maquinas']
            self.config['last_validation'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.config['grace_period_start'] = ""
            guardar_config_licencia(self.config, self.db_config)  # ✅ ESTO SE QUEDA

            messagebox.showinfo("✅ Éxito",
                            f"Licencia {info['license_type'].upper()} activada correctamente\n"
                            f"Válida hasta: {info['expires_at']}",
                            parent=self.ventana)
            self.resultado = self.config
            self.ventana.destroy()
        else:
            messagebox.showerror("❌ Error", f"Licencia no válida:\n{info}", parent=self.ventana)

    def iniciar_demo(self):
        if self.config['demo_used']:
            messagebox.showerror("Error", "Ya has utilizado el periodo de demo", parent=self.ventana)
            return

        exito, info = iniciar_demo(self.config['installation_id'])

        if exito:
            self.config['demo_used'] = True
            self.config['demo_start'] = datetime.now().strftime("%Y-%m-%d")
            self.config['demo_expires'] = info
            self.config['license_type'] = 'demo'
            guardar_config_licencia(self.config, self.db_config)

            messagebox.showinfo("🎁 Demo Activado",
                              f"Periodo de demo de 15 días activado\n"
                              f"Válido hasta: {info}\n\n"
                              f"Tendrás acceso a la versión PRO durante este periodo.",
                              parent=self.ventana)
            self.resultado = self.config
            self.ventana.destroy()
        else:
            messagebox.showerror("❌ Error", f"No se pudo iniciar demo:\n{info}", parent=self.ventana)

# ============================================================================
# ========== CLASES MODERNAS (sin cambios) ==========
# ============================================================================

class ModernButton(tk.Button):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.config(
            bg=COLORES["accento"],
            fg=COLORES["texto"],
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            bd=0,
            padx=20,
            pady=10,
            cursor="hand2"
        )
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        self.config(bg=self.lighten_color(COLORES["accento"]))

    def on_leave(self, e):
        self.config(bg=COLORES["accento"])

    def lighten_color(self, color, factor=0.2):
        if isinstance(color, str) and color.startswith('#'):
            color = color.lstrip('#')
            rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        else:
            rgb = color
        h, l, s = rgb_to_hls(rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0)
        l = min(1.0, l + factor)
        r, g, b = hls_to_rgb(h, l, s)
        return f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'

class ModernEntry(tk.Entry):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.config(
            bg=COLORES.get("superficie3", "#2d3047"),
            fg=COLORES["texto"],
            insertbackground=COLORES["texto"],
            relief="flat",
            bd=2,
            highlightbackground=COLORES["texto_secundario"],
            highlightcolor=COLORES["accento"],
            highlightthickness=1,
            font=("Segoe UI", 10),
            selectbackground=COLORES["accento"]
        )
        # Guardar referencia para actualizar después
        self.master = master

class ModernLabel(tk.Label):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.config(
            bg=COLORES["card"],
            fg=COLORES["texto"],
            font=("Segoe UI", 10)
        )

class ModernCombobox(ttk.Combobox):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.config(font=("Segoe UI", 10))
        self._actualizar_estilo()
    
    def _actualizar_estilo(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TCombobox",
                        fieldbackground=COLORES.get("superficie3", "#2d3047"),
                        background=COLORES.get("superficie3", "#2d3047"),
                        foreground=COLORES["texto"],
                        borderwidth=0,
                        relief="flat")
        style.map('TCombobox',
                  fieldbackground=[('readonly', COLORES.get("superficie3", "#2d3047"))],
                  selectbackground=[('readonly', COLORES["accento"])],
                  selectforeground=[('readonly', COLORES["texto"])])

class ModernFrame(tk.Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.config(bg=COLORES["fondo"])

# ============================================================================
# ========== CLASE PRINCIPAL AndonApp (MODIFICADA) ==========
# ============================================================================

class AndonApp:
    def __init__(self, root, config_inicial=None):
        self.root = root
        self.root.title("ReAction - Panel de Control")
        self.root.geometry("1400x800")
        self.root.configure(bg=COLORES_DEFAULT["fondo"])
        
        # Inicializar variables de control de proyección
        self.puede_configurar_proyeccion = False  # Valor por defecto
        self.ventana_proyeccion = None
        self.frame_tabla_proyeccion = None
        self.proj_counter = None
        self.timer_proyeccion = None
        
        # ===== Cargar configuraciones según el modo =====
        if config_inicial is None:
            # Modo normal: cargar configuración existente
            print("📂 Modo normal: cargando configuración desde archivos...")
            self.db_config = cargar_config_db()
            self.licencia_config = cargar_config_licencia(self.db_config)
            self.tipos_falla_data = cargar_tipos_falla(self.db_config)
            self.tipos_falla = [t["nombre"] for t in self.tipos_falla_data]
            self.config_sistema = cargar_config_sistema(self.db_config)
        else:
            # Modo instalación: usar la configuración proporcionada
            print(f"🔧 Modo instalación: usando configuración proporcionada")
            self.db_config = config_inicial.get('db_config', cargar_config_db())
            self.licencia_config = config_inicial.get('licencia_config', cargar_config_licencia(self.db_config))
            
            # Cargar tipos de falla de manera segura
            if 'tipos_falla_data' in config_inicial and config_inicial['tipos_falla_data']:
                self.tipos_falla_data = config_inicial['tipos_falla_data']
                print(f"✅ Tipos de falla cargados desde configuración: {len(self.tipos_falla_data)}")
            else:
                print("⚠️ No hay tipos_falla_data en configuración, cargando desde BD")
                self.tipos_falla_data = cargar_tipos_falla(self.db_config)
            
            self.tipos_falla = [t["nombre"] for t in self.tipos_falla_data]
            self.config_sistema = config_inicial.get('config_sistema', cargar_config_sistema(self.db_config))
            
            if "superficie3" not in self.config_sistema or not self.config_sistema["superficie3"]:
                self.config_sistema["superficie3"] = "#2d3047"  # valor por defecto
        
        # Cargar el tema activo o usar el predeterminado
        # Cargar el tema activo o usar el predeterminado
        tema_activo = self.config_sistema.get("tema_activo", "oscuro")

        # Verificar si el tema activo es uno de los predefinidos o es personalizado
        if tema_activo in TEMAS_PREDEFINIDOS:
            self.tema_actual = tema_activo
            self.es_tema_personalizado = False
            print(f"🎨 Tema predefinido cargado: {tema_activo}")
            # Obtener la paleta de colores del tema predefinido
            paleta_colores = TEMAS_PREDEFINIDOS[tema_activo]["colores"]
        else:
            # Si no es un tema predefinido, es personalizado
            self.tema_actual = "personalizado"
            self.es_tema_personalizado = True
            print(f"🎨 Tema personalizado cargado (basado en modificaciones)")
            # Para temas personalizados, usar los colores guardados en config_sistema
            # o los valores por defecto si no existen
            paleta_colores = {
                "fondo": self.config_sistema.get("color_fondo", "#1a1a2e"),
                "superficie1": self.config_sistema.get("color_sidebar", "#16213e"),
                "superficie2": self.config_sistema.get("color_card", "#0f3460"),
                "superficie3": self.config_sistema.get("superficie3", "#2d3047"),
                "texto_principal": self.config_sistema.get("texto_principal", "#ffffff"),
                "texto_secundario": self.config_sistema.get("texto_secundario", "#b0b0b0"),
                "acento_principal": self.config_sistema.get("acento_principal", "#e94560"),
                "exito": self.config_sistema.get("exito", "#00C853"),
                "advertencia": self.config_sistema.get("advertencia", "#FFC107"),
                "peligro": self.config_sistema.get("peligro", "#FF5252"),
                "pendiente": self.config_sistema.get("pendiente", "#FFA500")
            }

        # Inicializar el diccionario self.colores
        self.colores = {}

        # Mapear los colores del tema a las claves esperadas por el resto de la app
        for key, value in paleta_colores.items():
            self.colores[key] = value

        # Añadir mapeos antiguos para compatibilidad
        self.colores["sidebar"] = paleta_colores.get("superficie1", "#16213e")
        self.colores["card"] = paleta_colores.get("superficie2", "#0f3460")
        self.colores["texto"] = paleta_colores.get("texto_principal", "#ffffff")
        self.colores["texto_secundario"] = paleta_colores.get("texto_secundario", "#b0b0b0")
        self.colores["accento"] = paleta_colores.get("acento_principal", "#e94560")
        self.colores["exito"] = paleta_colores.get("exito", "#00C853")
        self.colores["warning"] = paleta_colores.get("advertencia", "#FFC107")
        self.colores["danger"] = paleta_colores.get("peligro", "#FF5252")
        self.colores["pendiente"] = paleta_colores.get("pendiente", "#FFA500")

        # Asegurar colores por defecto para los tipos de falla
        for k, v in COLORES_DEFAULT.items():
            if k not in self.colores:
                self.colores[k] = v

        # Guardamos la paleta completa para usarla más tarde si es necesario
        self.paleta_actual = paleta_colores
        
        self.paleta_actual.update({
            "fondo": self.colores.get("fondo", "#1a1a2e"),
            "superficie1": self.colores.get("sidebar", "#16213e"),
            "superficie2": self.colores.get("card", "#0f3460"),
            "superficie3": self.colores.get("superficie3", "#2d3047"),
            "texto_principal": self.colores.get("texto", "#ffffff"),
            "texto_secundario": self.colores.get("texto_secundario", "#b0b0b0"),
            "acento_principal": self.colores.get("accento", "#e94560"),
            "exito": self.colores.get("exito", "#00C853"),
            "advertencia": self.colores.get("warning", "#FFC107"),
            "peligro": self.colores.get("danger", "#FF5252"),
            "pendiente": self.colores.get("pendiente", "#FFA500")
        })
        
        # Colores del sistema
        for key in self.config_sistema:
            if key.startswith("color_"):
                color_key = key.replace("color_", "")
                self.colores[color_key] = self.config_sistema[key]
            elif key == "nombre_sistema":
                self.colores[key] = self.config_sistema[key]
        
        # Colores de los tipos de falla
        for tipo in self.tipos_falla_data:
            color_key = f"{tipo['nombre'].lower().replace(' ', '_')}_color"
            self.colores[color_key] = tipo['color']
            nombre_key = tipo['nombre'].lower().replace(' ', '_')
            if nombre_key not in self.colores:
                self.colores[nombre_key] = tipo['color']
        
        # Asegurar colores por defecto
        for k, v in COLORES_DEFAULT.items():
            if k not in self.colores:
                self.colores[k] = v
        
        if "pendiente" not in self.colores:
            self.colores["pendiente"] = "#FFA500"
        
        # ===== Cargar mapeo de botones =====
        print("🔍 Cargando mapeo de botones...")
        self.mapeo_botones = cargar_mapeo_botones(self.db_config)
        print(f"🔍 Mapeo cargado: {self.mapeo_botones}")

        print("🔧 Configuración DB:", self.db_config)

        # ===== Probar conexión =====
        self.db_estado = self.probar_conexion_inicial()
        self.mysql_disponible = self.db_estado
        self.intentos_reconexion = 0
        self.max_intentos_reconexion = 3
        self.tiempo_entre_reintentos = 30
        self.hilo_reconexion = None
        self.reconexion_activa = False

        # Configuración global de colores
        global COLORES
        COLORES = self.colores

        # ===== Cargar fallas activas =====
        self.fallas_activas = cargar_fallas_activas(self.db_config)
        self.debug_fallas_cargadas()
        print(f"🔄 Fallas activas recuperadas: {len(self.fallas_activas)}")
        
        # Depuración de estados
        print("📋 ESTADOS RECIÉN CARGADOS:")
        for i, falla in enumerate(self.fallas_activas):
            print(f"   {i+1}: M{falla['maquina']} - {falla['tipo']} - Estado: {falla.get('estado', 'SIN ESTADO')}")

        # ===== Inicializar variables =====
        self.ultimos_eventos = {}
        self.ventana_proyeccion = None
        self.frame_tabla_proyeccion = None
        self.nombre_sistema = COLORES.get("nombre_sistema", "ANDON SYSTEM")
        self.ultimos_resultados = []
        self.timer_proyeccion = None
        self.config_proyeccion = cargar_config_proyeccion(self.db_config)
        self.config_contador = cargar_config_contador(self.db_config)
        self.numeros_falla_asignados = {}
        self.mostrar_pendientes_proyeccion = tk.BooleanVar(value=True)

        # Asignar números de falla
        for falla in self.fallas_activas:
            if "numero_falla" not in falla:
                falla["numero_falla"] = self.obtener_siguiente_numero_falla()
            self.numeros_falla_asignados[id(falla)] = falla["numero_falla"]

        # ===== Configurar cierre de aplicación =====
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_aplicacion)
        atexit.register(self.guardar_estado_emergencia)

        try:
            import signal
            import sys
            signal.signal(signal.SIGTERM, self.manejador_senal)
            signal.signal(signal.SIGINT, self.manejador_senal)
        except:
            pass

        # ===== Inicializar UI =====
        self.setup_styles()
        self.create_main_layout()
        
        self.iniciar_lectura_red()
        self.iniciar_lectura_serial()
        
        # Iniciar actualización automática
        self.timer_auto_actualizacion = None
        self.iniciar_actualizacion_automatica()
        
        
        self.show_principal_view()
        
        self.iniciar_monitoreo()
        
        # Iniciar actualización automática
        self.timer_auto_actualizacion = None
        self.iniciar_actualizacion_automatica()

        self.root.bind('<F12>', lambda e: self.diagnosticar_base_datos())

        if not self.db_estado:
            self.mostrar_alerta_bd()

        if self.fallas_activas:
            self.root.after(500, self.mostrar_mensaje_recuperacion)

        # ===== LICENCIAMIENTO =====
        if config_inicial is None:
            # Modo normal: cargar desde BD
            print("🔍 Modo normal: cargando licencia desde BD...")
            self.licencia_config = cargar_config_licencia(self.db_config)
            self.licencia_valida, self.licencia_info = verificar_estado_licencia()

            while not self.licencia_valida:
                self.mostrar_ventana_activacion()
                self.licencia_config = cargar_config_licencia(self.db_config)
                self.licencia_valida, self.licencia_info = verificar_estado_licencia()

                if not self.licencia_valida:
                    # Preguntar si quiere diagnosticar
                    respuesta = messagebox.askyesno(
                        "Error de Licencia",
                        "No se pudo validar la licencia.\n\n"
                        "¿Quieres ejecutar un diagnóstico de red para verificar la conectividad?"
                    )
                    if respuesta:
                        self.mostrar_diagnostico()  # ← LLAMAR AL DIAGNÓSTICO
                    
                    resultado = messagebox.askretrycancel(
                        "Acceso Denegado",
                        "¿Quieres intentarlo de nuevo?"
                    )
                    if not resultado:
                        self.root.destroy()
                        return
        else:
            # Modo instalación: usar la licencia que ya tenemos
            print(f"🔧 Modo instalación: usando licencia proporcionada: {self.licencia_config.get('license_type')}")
            self.licencia_valida = True

        print(f"✅ Licencia válida. Tipo: {self.licencia_config.get('license_type')}")
        
        # Aplicar límites de licencia
        self.aplicar_limites_licencia()
        
        # Actualizar botones de pendientes (con un pequeño retraso para asegurar que la UI esté lista)
        self.root.after(200, self.actualizar_botones_pendientes)
        
        # Actualizar comboboxes
        if hasattr(self, 'tipos_frame'):
            print("🔄 Actualizando comboboxes de tipos...")
            self.actualizar_comboboxes_tipos()
        else:
            print("⚠️ tipos_frame aún no existe, se actualizará después")

        if self.licencia_config.get('license_type') == 'basic':
            print("🧹 Versión BASIC: Limpiando BD antes de cargar datos...")
            self.limpiar_fallas_inconclusas_basic()
            
    
            
    def mostrar_menu_licencia(self):
        MenuLicencia(self.root, self)

    def mostrar_ventana_activacion(self):
        ventana = VentanaActivacion(self.root, self.licencia_config, self.db_config)
        self.root.wait_window(ventana.ventana)
        if ventana.resultado:
            self.licencia_config = ventana.resultado
            self.licencia_valida = True
            
    #==============debug_carga_fallas==============
    def debug_carga_fallas(self):
        """Función de depuración para verificar el estado de las fallas al cargar"""
        print("\n=== DEBUG CARGA DE FALLAS ===")
        print(f"Total fallas activas cargadas: {len(self.fallas_activas)}")
        
        for i, falla in enumerate(self.fallas_activas):
            print(f"Falla {i+1}:")
            print(f"  Máquina: {falla.get('maquina')}")
            print(f"  Tipo: {falla.get('tipo')}")
            print(f"  Estado: {falla.get('estado')}")
            print(f"  Inicio: {falla.get('inicio')}")
            print(f"  Proceso: {falla.get('proceso')}")
            print(f"  Fin: {falla.get('fin')}")
            print(f"  Nota: {falla.get('nota_pendiente')}")
        
        print("===============================\n")
        
        # Verificar si alguna falla tiene fin pero estado no es resuelta
        inconsistentes = [f for f in self.fallas_activas if f.get("fin") and f.get("estado") != "resuelta"]
        if inconsistentes:
            print("⚠️ FALLAS INCONSISTENTES ENCONTRADAS:")
            for f in inconsistentes:
                print(f"  Máq: {f['maquina']}, Estado: {f.get('estado')}, Fin: {f.get('fin')}")
            
            # Corregir automáticamente
            for f in inconsistentes:
                f["estado"] = "resuelta"
                print(f"  ✅ Corregida falla de máquina {f['maquina']}")
            
            guardar_fallas_activas(self.fallas_activas, self.db_config)
            print("✅ Inconsistencias corregidas")
    
    #=============================================

    def aplicar_limites_licencia(self):
        tipo = self.licencia_config.get('license_type', 'basic')
        print(f"📊 Antes de aplicar límites - Fallas activas: {len(self.fallas_activas)}")
        print(f"🔄 Aplicando límites para licencia: {tipo}")

        # Definir TODAS las variables de permisos para cada tipo de licencia
        if tipo == 'basic':
            self.max_tipos_falla = self.licencia_config.get('max_fallas', 3)
            self.max_maquinas_permitidas = self.licencia_config.get('max_maquinas', 5)
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
            self.puede_usar_mysql = True  # Todos pueden usar MySQL

            # BASIC no debe recuperar fallas inconclusas
            if self.fallas_activas:
                print(f"🧹 BASIC: Eliminando {len(self.fallas_activas)} fallas inconclusas")
                try:
                    if self.db_config["tipo"] == "mysql" and self.mysql_disponible:
                        conn = self._conectar_mysql()
                        if conn:
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM fallas_activas")
                            conn.commit()
                            conn.close()
                    
                    print("✅ Fallas eliminadas de la BD")
                except Exception as e:
                    print(f"❌ Error eliminando fallas: {e}")
                
                # Limpiar la lista en memoria
                self.fallas_activas = []

        elif tipo == 'mid':
            self.max_tipos_falla = self.licencia_config.get('max_fallas', 4)
            self.max_maquinas_permitidas = self.licencia_config.get('max_maquinas', 15)
            self.puede_configurar = True
            self.puede_ver_graficos = True
            self.puede_exportar_excel_con_graficos = True
            self.excel_una_vez_dia = False
            self.puede_generar_esp32 = False
            self.puede_configurar_proyeccion = True
            self.recupera_fallas = True
            self.reset_consecutivo = "configurable"
            self.puede_usar_pendientes = True
            self.puede_agregar_notas = False
            self.puede_ver_pendientes = True
            self.puede_filtrar_tipos_graficas = False 
            self.puede_ajustar_periodo_estadisticas = False
            self.dias_tendencia_predeterminados = 7 
            self.puede_usar_mysql = True

        elif tipo == 'pro' or tipo == 'demo':
            self.max_tipos_falla = self.licencia_config.get('max_fallas', 5)
            self.max_maquinas_permitidas = self.licencia_config.get('max_maquinas', 200)
            self.puede_configurar = True
            self.puede_ver_graficos = True
            self.puede_exportar_excel_con_graficos = True
            self.excel_una_vez_dia = False
            self.puede_generar_esp32 = True
            self.puede_configurar_proyeccion = True
            self.recupera_fallas = True
            self.reset_consecutivo = "configurable"
            self.puede_usar_pendientes = True
            self.puede_agregar_notas = True
            self.puede_ver_pendientes = True
            self.puede_filtrar_tipos_graficas = True  
            self.puede_ajustar_periodo_estadisticas = True  
            self.dias_tendencia_predeterminados = 7
            self.puede_usar_mysql = True
        
        print(f"📊 Después de aplicar límites - Fallas activas: {len(self.fallas_activas)}")

        global MAQUINAS
        MAQUINAS = [str(i) for i in range(1, self.max_maquinas_permitidas + 1)]

        # Recortar la lista de tipos de falla si es necesario
        if len(self.tipos_falla) > self.max_tipos_falla:
            print(f"⚠️ Recortando tipos de falla de {len(self.tipos_falla)} a {self.max_tipos_falla}")
            self.tipos_falla = self.tipos_falla[:self.max_tipos_falla]
            self.tipos_falla_data = self.tipos_falla_data[:self.max_tipos_falla]
            COLORES["fallas"] = self.tipos_falla
            print(f"⚠️ Tipos de falla recortados a {self.max_tipos_falla} según licencia.")
        else:
            print(f"✅ Tipos de falla dentro del límite: {len(self.tipos_falla)}/{self.max_tipos_falla}")

        print(f"✅ Licencia {tipo.upper()} aplicada")
        print(f"   Máquinas: {self.max_maquinas_permitidas}, Tipos de falla: {self.max_tipos_falla}")
        print(f"   Puede usar pendientes: {self.puede_usar_pendientes}")
        print(f"   Puede agregar notas: {self.puede_agregar_notas}")
        
        # Actualizar botones de pendientes
        if hasattr(self, 'pendientes_btn_frame'):
            # Programar la actualización después de que la interfaz esté lista
            self.root.after(100, self.actualizar_botones_pendientes)
        else:
            print("⚠️ pendientes_btn_frame no existe todavía")
    
    def actualizar_botones_pendientes(self):
        """Actualiza la visibilidad de los botones de pendientes según la licencia"""
        try:
            # Limpiar frame de botones de pendientes
            for widget in self.pendientes_btn_frame.winfo_children():
                widget.destroy()
            
            # Verificar si puede ver pendientes
            puede_ver = hasattr(self, 'puede_ver_pendientes') and self.puede_ver_pendientes
            
            print(f"🔍 Actualizando botones de pendientes - puede_ver={puede_ver}")
            
            if puede_ver:
                print(f"✅ Mostrando botones de pendientes")
                
                # Variable para controlar visibilidad de pendientes
                if not hasattr(self, 'ocultar_pendientes_var'):
                    self.ocultar_pendientes_var = tk.BooleanVar(value=False)
                
                # Botón VER PENDIENTES
                btn_pendientes = tk.Button(self.pendientes_btn_frame,
                        text="📋 PENDIENTES",
                        bg=COLORES.get("pendiente", "#FFA500"),
                        fg=COLORES["negro"],
                        font=("Segoe UI", 9, "bold"),
                        relief="flat",
                        padx=8,
                        pady=3,
                        cursor="hand2",
                        command=self.ver_fallas_pendientes)
                btn_pendientes.pack(side="left", padx=2)
                
                # Botón para ocultar/mostrar pendientes en tabla principal
                btn_ocultar = tk.Button(self.pendientes_btn_frame,
                        text="👁️ OCULTAR",
                        bg=COLORES["card"],
                        fg=COLORES["texto"],
                        font=("Segoe UI", 9),
                        relief="flat",
                        padx=8,
                        pady=3,
                        cursor="hand2",
                        command=self.toggle_ocultar_pendientes)
                btn_ocultar.pack(side="left", padx=2)
                
                # Empaquetar el frame en la posición correcta
                # Lo colocamos después del botón de sincronización si existe, si no, al final
                try:
                    self.pendientes_btn_frame.pack(side="right", padx=2)
                except Exception as e:
                    print(f"Error al empaquetar frame de pendientes: {e}")
                    self.pendientes_btn_frame.pack(side="right", padx=2)
                
                # Forzar actualización
                self.pendientes_btn_frame.update()
                
            else:
                print(f"❌ Ocultando botones de pendientes")
                self.pendientes_btn_frame.pack_forget()
                
        except Exception as e:
            print(f"Error actualizando botones de pendientes: {e}")
            import traceback
            traceback.print_exc()

    def verificar_limite_maquina(self, maquina):
        if not verificar_limite_maquinas(self.licencia_config, maquina):
            messagebox.showwarning("Límite de Máquinas",
                                f"La máquina {maquina} excede el límite de "
                                f"{self.max_maquinas_permitidas} máquinas\n"
                                "permitidas para tu licencia.")
            return False
        return True

    def limpiar_fallas_inconclusas_basic(self):
        """Elimina fallas inconclusas de MySQL (solo para BASIC)"""
        print("🧹 BASIC: Limpiando fallas inconclusas de la base de datos...")
        
        try:
            if not self.mysql_disponible:
                print("❌ MySQL no disponible")
                return
                
            conn = self._conectar_mysql()
            if conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM fallas WHERE fin IS NULL OR fin = ''")
                eliminadas = cursor.rowcount
                conn.commit()
                conn.close()
                print(f"✅ Eliminadas {eliminadas} fallas inconclusas")
                
                if eliminadas > 0:
                    self.root.after(1000, lambda: messagebox.showinfo(
                        "🧹 Limpieza Automática (BASIC)",
                        f"Se han eliminado {eliminadas} fallas inconclusas."
                    ))
        except Exception as e:
            print(f"❌ Error en limpieza: {e}")

    def probar_conexion_inicial(self):
        """Prueba la conexión sin bloquear - retorna inmediatamente"""
        if self.db_config["tipo"] == "mysql":
            print("🔄 Iniciando verificación de MySQL en segundo plano...")
            
            def verificar():
                try:
                    conn = self._conectar_mysql(timeout=2)
                    if conn:
                        conn.close()
                        self.mysql_disponible = True
                        self.db_estado = True
                        print("✅ MySQL disponible (verificación rápida)")
                    else:
                        self.mysql_disponible = False
                        self.db_estado = False
                        print("⚠️ MySQL no disponible")
                except Exception as e:
                    self.mysql_disponible = False
                    self.db_estado = False
                    print(f"⚠️ Error verificando MySQL: {e}")
            
            threading.Thread(target=verificar, daemon=True).start()
            return True
        else:
            # Esto ya no debería ocurrir, pero por si acaso
            print("⚠️ ADVERTENCIA: db_config no es MySQL, forzando a False")
            return False
    
    def mostrar_alerta_bd(self):
        messagebox.showerror(
            "❌ Error de Conexión",
            "No se pudo conectar a la base de datos MySQL.\n\n"
            "Verifica:\n"
            "• Que el servidor MySQL esté accesible\n"
            "• Los datos de conexión en Configuración\n"
            "• Tu conexión a internet (si es remoto)\n\n"
            "La aplicación se cerrará."
        )
        self.root.destroy()  # Forzar cierre si no hay BD

    def manejador_senal(self, signum, frame):
        print(f"📢 Señal de cierre recibida: {signum}")
        self.guardar_estado_emergencia()
        sys.exit(0)

    def guardar_estado_emergencia(self):
        print("⚠️ Guardando estado de emergencia...")
        guardar_fallas_activas(self.fallas_activas, self.db_config)
        print("✅ Estado de emergencia guardado")

    def cerrar_aplicacion(self):
        print("🔄 Cerrando aplicación...")
        
        # Cancelar timer de actualización automática
        if hasattr(self, 'timer_auto_actualizacion') and self.timer_auto_actualizacion:
            try:
                self.root.after_cancel(self.timer_auto_actualizacion)
            except:
                pass
            self.timer_auto_actualizacion = None
        
        # ✅ SOLO guardar fallas activas al cerrar
        guardar_fallas_activas(self.fallas_activas, self.db_config)
        
        self.root.destroy()

    def mostrar_mensaje_recuperacion(self):
        mensaje = f"Se han recuperado {len(self.fallas_activas)} falla(s) activa(s) de la sesión anterior.\n\n"
        mensaje += "Puedes continuar procesándolas normalmente."

        messagebox.showinfo("🔄 Fallas Recuperadas", mensaje)

        self.actualizar_tabla()
        self.update_stats()

    def cerrar_todas_fallas_activas(self):
        if not self.fallas_activas:
            messagebox.showinfo("Información", "No hay fallas activas para cerrar.")
            return

        respuesta = messagebox.askyesno(
            "Confirmar",
            f"¿Estás seguro de cerrar TODAS las {len(self.fallas_activas)} fallas activas?\n\n"
            "Se registrarán con la hora actual como fin."
        )

        if respuesta:
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            fallas_cerradas = 0

            fallas_a_cerrar = self.fallas_activas.copy()

            for alerta in fallas_a_cerrar:
                try:
                    if "proceso" not in alerta or not alerta["proceso"]:
                        alerta["proceso"] = ahora

                    alerta["fin"] = ahora

                    if guardar_falla(alerta, self.db_config):
                        fallas_cerradas += 1
                        print(f"✅ Falla cerrada y guardada en {self.db_config['tipo']}")
                    else:
                        print(f"❌ Error guardando falla")

                    if alerta in self.fallas_activas:
                        self.fallas_activas.remove(alerta)

                    if id(alerta) in self.numeros_falla_asignados:
                        del self.numeros_falla_asignados[id(alerta)]

                except Exception as e:
                    print(f"❌ Error cerrando falla: {e}")

            print(f"✅ Cerradas {fallas_cerradas} fallas. Activas restantes: {len(self.fallas_activas)}")

            self.actualizar_tabla()
            self.update_stats()

            if self.ventana_proyeccion and self.frame_tabla_proyeccion:
                self.actualizar_tabla_proyeccion()
                if hasattr(self, 'proj_counter'):
                    self.proj_counter.config(text=str(len(self.fallas_activas)))

            guardar_fallas_activas(self.fallas_activas, self.db_config)

            self.root.update_idletasks()
            self.root.update()

            messagebox.showinfo("✅ Completado",
                            f"Se cerraron {fallas_cerradas} fallas correctamente.\n"
                            f"Registradas con fecha: {ahora}")

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview",
                        background=COLORES["card"],
                        foreground=COLORES["texto"],
                        rowheight=35,
                        fieldbackground=COLORES["card"],
                        borderwidth=0,
                        font=("Segoe UI", 10))
        style.configure("Treeview.Heading",
                        background=COLORES["sidebar"],
                        foreground=COLORES["texto"],
                        relief="flat",
                        borderwidth=0,
                        font=("Segoe UI", 11, "bold"))
        style.map('Treeview',
                  background=[('selected', COLORES["accento"])],
                  foreground=[('selected', COLORES["texto"])])
        style.configure("Vertical.TScrollbar",
                        background=COLORES["sidebar"],
                        troughcolor=COLORES["fondo"],
                        borderwidth=0,
                        relief="flat")

    def generar_codigo_esp32(self):
        if not self.puede_generar_esp32:
            messagebox.showinfo("Acceso Restringido",
                            "La generación de código ESP32\n"
                            "requiere licencia PRO.")
            return

        config_window = tk.Toplevel(self.root)
        config_window.title("Generar Código ESP32")
        config_window.geometry("600x700")
        config_window.configure(bg=COLORES["fondo"])
        config_window.resizable(False, False)

        config_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (600 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (700 // 2)
        config_window.geometry(f"+{x}+{y}")

        tk.Label(config_window,
                text="⚙️ Generar Código para ESP32",
                bg=COLORES["fondo"],
                fg=COLORES["texto"],
                font=("Segoe UI", 18, "bold")).pack(pady=20)

        main_frame = tk.Frame(config_window, bg=COLORES["fondo"])
        main_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        canvas = tk.Canvas(main_frame, bg=COLORES["fondo"], highlightthickness=0, height=500)
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORES["fondo"])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        tk.Label(scrollable_frame,
                text="Número de Máquina:",
                bg=COLORES["fondo"],
                fg=COLORES["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 10))

        maquina_frame = tk.Frame(scrollable_frame, bg=COLORES["fondo"])
        maquina_frame.pack(fill="x", pady=(0, 20))

        self.esp32_numero = tk.StringVar(value="1")
        tk.Spinbox(maquina_frame,
                from_=1, to=99,
                textvariable=self.esp32_numero,
                width=5,
                bg="#2d3047",
                fg=COLORES["texto"],
                font=("Segoe UI", 10),
                relief="flat").pack(side="left", padx=(0, 10))

        tk.Label(maquina_frame,
                text=f"IP: 192.168.1.{101 + int(self.esp32_numero.get()) - 1}",
                bg=COLORES["fondo"],
                fg=COLORES["texto_secundario"],
                font=("Segoe UI", 10)).pack(side="left")

        tk.Label(scrollable_frame,
                text="Pines del ESP32 (W5500 ocupando D23, D19, D18, D5, D4):",
                bg=COLORES["fondo"],
                fg=COLORES["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 10))

        pines_esp32 = {
            "D14": True, "D27": True, "D26": True, "D25": True, "D33": True,
            "D32": False, "D15": False, "D2": False, "D13": False, "D12": False,
            "RX2": False, "TX2": False, "D21": False, "D22": False,
            "D23": True, "D19": True, "D18": True, "D5": True, "D4": True,
            "D34": False, "D35": False, "VP": False, "VN": False,
        }

        pines_w5500 = ["D23", "D19", "D18", "D5", "D4"]

        pines_frame = tk.Frame(scrollable_frame, bg=COLORES["card"])
        pines_frame.pack(fill="x", pady=(0, 20))

        w5500_frame = tk.Frame(pines_frame, bg=COLORES["card"])
        w5500_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(w5500_frame,
                text="🔌 W5500 (Obligatorios):",
                bg=COLORES["card"],
                fg=COLORES["danger"],
                font=("Segoe UI", 10, "bold")).pack(anchor="w")

        w5500_pins_frame = tk.Frame(w5500_frame, bg=COLORES["card"])
        w5500_pins_frame.pack(fill="x", pady=5)

        for i, pin in enumerate(pines_w5500):
            tk.Label(w5500_pins_frame,
                    text=f"{pin}",
                    bg=COLORES["danger"],
                    fg=COLORES["texto"],
                    font=("Segoe UI", 8),
                    width=5,
                    relief="flat").pack(side="left", padx=2)

        botones_frame = tk.Frame(pines_frame, bg=COLORES["card"])
        botones_frame.pack(fill="x", padx=10, pady=(0, 10))

        tk.Label(botones_frame,
                text="🎚️ Pines para Botones:",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 10))

        self.pin_assignments = {}
        pines_sugeridos = ["D14", "D27", "D26", "D25", "D33", "D32", "D15", "D2", "D13", "D12"]

        for i, tipo in enumerate(self.tipos_falla):
            tipo_frame = tk.Frame(botones_frame, bg=COLORES["card"])
            tipo_frame.pack(fill="x", pady=2)

            tk.Label(tipo_frame,
                    text=f"{tipo}:",
                    bg=COLORES["card"],
                    fg=COLORES["texto"],
                    font=("Segoe UI", 9),
                    width=15,
                    anchor="w").pack(side="left", padx=(0, 10))

            pin_var = tk.StringVar(value=pines_sugeridos[i] if i < len(pines_sugeridos) else "D32")
            combobox = ttk.Combobox(tipo_frame,
                                textvariable=pin_var,
                                values=[pin for pin, ocupado in pines_esp32.items() if not ocupado] + [pines_sugeridos[i] if i < len(pines_sugeridos) else "D32"],
                                width=8,
                                state="readonly")
            combobox.pack(side="left")

            status_frame = tk.Frame(tipo_frame, bg=COLORES["card"])
            status_frame.pack(side="left", padx=10)

            status_label = tk.Label(status_frame,
                                text="●",
                                fg="#4CAF50" if pines_esp32.get(pin_var.get(), True) else "#FF5252",
                                bg=COLORES["card"],
                                font=("Arial", 10))
            status_label.pack(side="left")

            tk.Label(status_frame,
                    text="Ocupado" if pines_esp32.get(pin_var.get(), True) else "Libre",
                    bg=COLORES["card"],
                    fg=COLORES["texto_secundario"],
                    font=("Segoe UI", 8)).pack(side="left", padx=5)

            self.pin_assignments[tipo] = {
                "var": pin_var,
                "status": status_label,
                "combobox": combobox
            }

            def update_status(event=None, t=tipo):
                pin = self.pin_assignments[t]["var"].get()
                ocupado = pin in pines_w5500 or pin in [ass["var"].get() for name, ass in self.pin_assignments.items() if name != t]
                color = "#FF5252" if ocupado else "#4CAF50"
                texto = "Ocupado" if ocupado else "Libre"
                self.pin_assignments[t]["status"].config(fg=color)
                self.pin_assignments[t]["status"].master.children['!label'].config(text=texto)

            combobox.bind("<<ComboboxSelected>>", update_status)

        tk.Label(scrollable_frame,
                text="IP del Servidor (PC con Andon):",
                bg=COLORES["fondo"],
                fg=COLORES["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(20, 10))

        server_frame = tk.Frame(scrollable_frame, bg=COLORES["fondo"])
        server_frame.pack(fill="x", pady=(0, 20))

        self.esp32_server_ip = tk.StringVar(value="192.168.1.10")
        tk.Entry(server_frame,
                textvariable=self.esp32_server_ip,
                width=20,
                bg="#2d3047",
                fg=COLORES["texto"],
                font=("Segoe UI", 10),
                relief="flat").pack(side="left")

        tk.Button(server_frame,
                text="Mi IP Actual",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 8),
                relief="flat",
                padx=10,
                cursor="hand2",
                command=self.obtener_ip_actual).pack(side="left", padx=10)

        tk.Label(scrollable_frame,
                text="Vista Previa del Código:",
                bg=COLORES["fondo"],
                fg=COLORES["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(20, 10))

        code_preview = tk.Text(scrollable_frame,
                            height=15,
                            width=50,
                            bg="#1e1e1e",
                            fg="#d4d4d4",
                            font=("Consolas", 9),
                            relief="flat",
                            wrap="none")
        code_preview.pack(fill="x", pady=(0, 20))

        code_scroll_x = tk.Scrollbar(scrollable_frame, orient="horizontal", command=code_preview.xview)
        code_preview.configure(xscrollcommand=code_scroll_x.set)
        code_scroll_x.pack(fill="x", pady=(0, 10))

        self.actualizar_vista_previa(code_preview)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        button_frame = tk.Frame(config_window, bg=COLORES["fondo"])
        button_frame.pack(fill="x", padx=20, pady=(0, 20))

        tk.Button(button_frame,
                text="🔄 Actualizar Vista Previa",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 10),
                relief="flat",
                padx=15,
                pady=8,
                cursor="hand2",
                command=lambda: self.actualizar_vista_previa(code_preview)).pack(side="left", padx=5)

        tk.Button(button_frame,
                text="💾 Generar Archivo .ino",
                bg=COLORES["success"],
                fg=COLORES["texto"],
                font=("Segoe UI", 11, "bold"),
                relief="flat",
                padx=20,
                pady=10,
                cursor="hand2",
                command=lambda: self.guardar_codigo_esp32(config_window)).pack(side="right", padx=5)

        tk.Button(button_frame,
                text="🚫 Cancelar",
                bg=COLORES["danger"],
                fg=COLORES["texto"],
                font=("Segoe UI", 11),
                relief="flat",
                padx=20,
                pady=10,
                cursor="hand2",
                command=config_window.destroy).pack(side="right", padx=5)

    def obtener_ip_actual(self):
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            self.esp32_server_ip.set(ip)
        except:
            messagebox.showerror("Error", "No se pudo obtener la IP actual")

    def actualizar_vista_previa(self, code_widget):
        num_maquina = int(self.esp32_numero.get())
        ip_octet = 100 + num_maquina
        mac_suffix = f"{num_maquina:02X}"
        
        pines = []
        for tipo in self.tipos_falla:
            if tipo in self.pin_assignments:
                pin_str = self.pin_assignments[tipo]["var"].get()
                pin_num = pin_str.replace("D", "") if pin_str.startswith("D") else pin_str
                pines.append(pin_num)
        
        # Generar el código línea por línea SIN NINGUNA indentación
        lineas = []
        lineas.append("#include <SPI.h>")
        lineas.append("#include <Ethernet.h>")
        lineas.append("")
        lineas.append(f"const int numeroMaquina = {num_maquina};")
        lineas.append(f"const int numBotones = {len(pines)};")
        lineas.append("")
        lineas.append(f"const int botones[] = {{{', '.join(pines)}}};")
        lineas.append("")
        lineas.append("#define PIN_CS  5")
        lineas.append("#define PIN_RST 4")
        lineas.append("")
        lineas.append(f"byte mac[] = {{ 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0x{mac_suffix} }};")
        lineas.append(f"IPAddress ip(192, 168, 1, {ip_octet});")
        lineas.append(f"IPAddress serverIP({self.esp32_server_ip.get().replace('.', ', ')});")
        lineas.append("const uint16_t serverPort = 5000;")
        lineas.append("")
        lineas.append("EthernetClient client;")
        lineas.append(f"bool estadoAnterior[numBotones] = {{false}};")
        lineas.append("")
        lineas.append("void setup() {")
        lineas.append("    Serial.begin(115200);")
        lineas.append("    Serial.println(\"Máquina \" + String(numeroMaquina));")
        lineas.append("")
        lineas.append("    Ethernet.init(PIN_CS);")
        lineas.append("    Ethernet.begin(mac, ip);")
        lineas.append("")
        lineas.append("    Serial.print(\"IP: \");")
        lineas.append("    Serial.println(Ethernet.localIP());")
        lineas.append("")
        lineas.append("    for (int i = 0; i < numBotones; i++) {")
        lineas.append("        pinMode(botones[i], INPUT_PULLUP);")
        lineas.append("        Serial.print(\"Botón \");")
        lineas.append("        Serial.print(i+1);")
        lineas.append("        Serial.print(\" en pin D\");")
        lineas.append("        Serial.println(botones[i]);")
        lineas.append("    }")
        lineas.append("}")
        lineas.append("")
        lineas.append("void loop() {")
        lineas.append("    for (int i = 0; i < numBotones; i++) {")
        lineas.append("        bool presionado = (digitalRead(botones[i]) == LOW);")
        lineas.append("        if (presionado && !estadoAnterior[i]) {")
        lineas.append("            enviarEvento(i+1);")
        lineas.append("        }")
        lineas.append("        estadoAnterior[i] = presionado;")
        lineas.append("    }")
        lineas.append("    delay(50);")
        lineas.append("}")
        lineas.append("")
        lineas.append("void enviarEvento(int numeroBoton) {")
        lineas.append("    Serial.print(\"Evento: Botón \");")
        lineas.append("    Serial.println(numeroBoton);")
        lineas.append("")
        lineas.append("    if (client.connect(serverIP, serverPort)) {")
        lineas.append("        String mensaje = String(numeroMaquina) + \"|Boton\" + String(numeroBoton) + \"\\n\";")
        lineas.append("        client.print(mensaje);")
        lineas.append("        client.stop();")
        lineas.append("        Serial.println(\"✓ Enviado\");")
        lineas.append("    } else {")
        lineas.append("        Serial.println(\"✗ Error conexión\");")
        lineas.append("    }")
        lineas.append("}")
        
        # Unir todas las líneas con saltos de línea
        codigo = "\n".join(lineas)
        
        # Limpiar y insertar el código
        code_widget.delete(1.0, tk.END)
        code_widget.insert(1.0, codigo)
    
    def guardar_codigo_esp32(self, window):
        num_maquina = self.esp32_numero.get()
        file_path = filedialog.asksaveasfilename(
            defaultextension=".ino",
            initialfile=f"andon_maquina_{num_maquina}.ino",
            filetypes=[("Arduino files", "*.ino"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        # Buscar el widget de código
        code_widget = None
        for widget in window.winfo_children():
            if isinstance(widget, tk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, tk.Canvas):
                        for grandchild in child.winfo_children():
                            if isinstance(grandchild, tk.Frame):
                                for text_widget in grandchild.winfo_children():
                                    if isinstance(text_widget, tk.Text):
                                        code_widget = text_widget
                                        break
        
        if code_widget:
            # Obtener el código y eliminar cualquier espacio al inicio de cada línea
            codigo_raw = code_widget.get(1.0, tk.END)
            lineas = codigo_raw.split('\n')
            # Eliminar espacios en blanco al inicio de cada línea que no sean parte de la indentación del código
            lineas_procesadas = []
            for linea in lineas:
                # Mantener la indentación de 4 espacios para el código dentro de las funciones
                # pero eliminar cualquier indentación adicional al principio del archivo
                if linea.startswith('    '):  # Esto es indentación válida
                    lineas_procesadas.append(linea)
                else:
                    lineas_procesadas.append(linea.lstrip())  # Eliminar espacios al inicio
            
            codigo_limpio = '\n'.join(lineas_procesadas).strip()
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(codigo_limpio)
                messagebox.showinfo("✅ Código Generado", f"Archivo guardado en:\n{file_path}")
                window.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar el archivo:\n{str(e)}")
        else:
            messagebox.showerror("Error", "No se encontró el código generado")
              
    #=======================fallos pendientes================================
    
    # Agregar estos métodos a la clase AndonApp
    def mostrar_dialogo_nota_pendiente(self, alerta):
        """Muestra un diálogo para agregar nota a una falla pendiente"""
        if not self.puede_usar_pendientes and not self.puede_agregar_notas:
            messagebox.showinfo("Acceso Restringido",
                            "Las fallas pendientes son una característica\n"
                            "disponible solo en licencias MID y PRO.",
                            parent=self.root)
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Nota de Falla Pendiente")
        dialog.geometry("500x450")
        dialog.configure(bg=COLORES["fondo"])
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (500 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (450 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Título
        tk.Label(dialog,
                text="📝 Marcar como Pendiente",
                bg=COLORES["fondo"],
                fg=COLORES["texto"],
                font=("Segoe UI", 16, "bold")).pack(pady=20)
        
        # Información de la falla
        info_frame = tk.Frame(dialog, bg=COLORES["card"])
        info_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(info_frame,
                text=f"Máquina: {alerta['maquina']}",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=10, pady=5)
        
        tk.Label(info_frame,
                text=f"Tipo: {alerta['tipo']}",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 11)).pack(anchor="w", padx=10, pady=5)
        
        # Área de nota
        tk.Label(dialog,
                text="Nota / Motivo del pendiente:",
                bg=COLORES["fondo"],
                fg=COLORES["texto"],
                font=("Segoe UI", 11, "bold")).pack(pady=(20, 5))
        
        texto_nota = tk.Text(dialog,
                            height=8,
                            width=50,
                            bg="#2d3047",
                            fg=COLORES["texto"],
                            font=("Segoe UI", 10),
                            wrap="word")
        texto_nota.pack(padx=20, pady=5)
        
        # Si ya existe una nota, mostrarla - CORREGIDO: usar 1.0 sin comillas
        if "nota_pendiente" in alerta and alerta["nota_pendiente"]:
            texto_nota.insert(1.0, alerta["nota_pendiente"])
        
        # Frame para botones
        btn_frame = tk.Frame(dialog, bg=COLORES["fondo"])
        btn_frame.pack(pady=20)
        
        def guardar_nota():
            nota = texto_nota.get(1.0, tk.END).strip()
            if nota:
                alerta["nota_pendiente"] = nota
                alerta["estado"] = "pendiente"
                alerta["fecha_pendiente"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Guardar en BD
                guardar_falla(alerta, self.db_config)
                guardar_fallas_activas(self.fallas_activas, self.db_config)
                
                self.actualizar_tabla()
                self.update_stats()
                
                if self.ventana_proyeccion and self.frame_tabla_proyeccion:
                    self.actualizar_tabla_proyeccion()
                
                dialog.destroy()
                messagebox.showinfo("✅ Nota Guardada", 
                                "La falla ha sido marcada como pendiente.")
            else:
                messagebox.showwarning("Aviso", 
                                    "Debes agregar una nota explicativa.", 
                                    parent=dialog)
        
        tk.Button(btn_frame,
                text="💾 Guardar y Marcar Pendiente",
                bg=COLORES["warning"],
                fg=COLORES["negro"],
                font=("Segoe UI", 11, "bold"),
                relief="flat",
                padx=20,
                pady=8,
                cursor="hand2",
                command=guardar_nota).pack(side="left", padx=5)
        
        tk.Button(btn_frame,
                text="❌ Cancelar",
                bg=COLORES["danger"],
                fg=COLORES["texto"],
                font=("Segoe UI", 11),
                relief="flat",
                padx=20,
                pady=8,
                cursor="hand2",
                command=dialog.destroy).pack(side="left", padx=5)
        
    def actualizar_desde_bd(self):
        """Actualiza manualmente todas las fallas desde la base de datos"""
        print("🔄 Actualizando datos desde la base de datos...")
        
        try:
            # Guardar estado actual de fallas activas
            fallas_anteriores = self.fallas_activas.copy()
            
            # Recargar fallas activas desde la BD
            self.fallas_activas = cargar_fallas_activas(self.db_config)
            
            print(f"📊 Fallas activas antes: {len(fallas_anteriores)}, después: {len(self.fallas_activas)}")
            
            # Verificar y agregar notas que puedan haber venido de Android
            notas_recuperadas = 0
            for falla in self.fallas_activas:
                if "nota_pendiente" in falla and falla["nota_pendiente"]:
                    notas_recuperadas += 1
                    print(f"📝 Nota encontrada: M{falla['maquina']} - {falla['tipo']}: {falla['nota_pendiente'][:50]}...")
            
            print(f"📝 Notas recuperadas: {notas_recuperadas}")
            
            # Actualizar UI
            self.actualizar_tabla()
            
            # ✅ Verificar que la ventana principal existe antes de update_stats
            if self.root and self.root.winfo_exists():
                self.update_stats()
            
            if self.ventana_proyeccion and self.ventana_proyeccion.winfo_exists():
                self.actualizar_tabla_proyeccion()
            
            messagebox.showinfo("✅ Actualización Completada",
                            f"Se actualizaron {len(self.fallas_activas)} fallas activas.\n"
                            f"Notas encontradas: {notas_recuperadas}",
                            parent=self.root)
            
        except Exception as e:
            print(f"❌ Error en actualización manual: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"No se pudo actualizar: {str(e)}", parent=self.root)

    def mostrar_dialogo_nota(self, alerta):
        """Muestra un diálogo para agregar/editar nota a cualquier falla (solo PRO)"""
        if not self.puede_agregar_notas:
            messagebox.showinfo("Acceso Restringido",
                            "Agregar notas solo está disponible\n"
                            "en licencias PRO.",
                            parent=self.root)
            return
            
        dialog = tk.Toplevel(self.root)
        dialog.title("Nota de Falla")
        dialog.geometry("500x450")
        dialog.configure(bg=COLORES["fondo"])
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (500 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (450 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Título
        tk.Label(dialog,
                text="📝 Agregar/Editar Nota",
                bg=COLORES["fondo"],
                fg=COLORES["texto"],
                font=("Segoe UI", 16, "bold")).pack(pady=20)
        
        # Información de la falla
        info_frame = tk.Frame(dialog, bg=COLORES["card"])
        info_frame.pack(fill="x", padx=20, pady=10)
        
        estado_text = ""
        if alerta.get("estado") == "pendiente":
            estado_text = " (Pendiente)"
        
        tk.Label(info_frame,
                text=f"Máquina: {alerta['maquina']}{estado_text}",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=10, pady=5)
        
        tk.Label(info_frame,
                text=f"Tipo: {alerta['tipo']}",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 11)).pack(anchor="w", padx=10, pady=5)
        
        # Área de nota
        tk.Label(dialog,
                text="Nota:",
                bg=COLORES["fondo"],
                fg=COLORES["texto"],
                font=("Segoe UI", 11, "bold")).pack(pady=(20, 5))
        
        texto_nota = tk.Text(dialog,
                            height=8,
                            width=50,
                            bg="#2d3047",
                            fg=COLORES["texto"],
                            font=("Segoe UI", 10),
                            wrap="word")
        texto_nota.pack(padx=20, pady=5)
        
        # Si ya existe una nota, mostrarla - CORREGIDO: usar "1.0" con comillas
        if "nota_pendiente" in alerta and alerta["nota_pendiente"]:
            texto_nota.insert("1.0", alerta["nota_pendiente"])
        elif "nota" in alerta and alerta["nota"]:
            texto_nota.insert("1.0", alerta["nota"])
        
        # Frame para botones
        btn_frame = tk.Frame(dialog, bg=COLORES["fondo"])
        btn_frame.pack(pady=20)
        
        def guardar_nota():
            nota = texto_nota.get("1.0", tk.END).strip()
            if nota:
                alerta["nota_pendiente"] = nota
                # No cambiar el estado, solo agregar nota
                
                # Guardar en BD
                guardar_falla(alerta, self.db_config)
                guardar_fallas_activas(self.fallas_activas, self.db_config)
                
                self.actualizar_tabla()
                self.update_stats()
                
                if self.ventana_proyeccion and self.frame_tabla_proyeccion:
                    self.actualizar_tabla_proyeccion()
                
                dialog.destroy()
                messagebox.showinfo("✅ Nota Guardada", 
                                "Nota agregada correctamente.")
            else:
                messagebox.showwarning("Aviso", 
                                    "La nota no puede estar vacía.", 
                                    parent=dialog)
        
        tk.Button(btn_frame,
                text="💾 Guardar Nota",
                bg=COLORES["success"],
                fg=COLORES["texto"],
                font=("Segoe UI", 11, "bold"),
                relief="flat",
                padx=20,
                pady=8,
                cursor="hand2",
                command=guardar_nota).pack(side="left", padx=5)
        
        tk.Button(btn_frame,
                text="❌ Cancelar",
                bg=COLORES["danger"],
                fg=COLORES["texto"],
                font=("Segoe UI", 11),
                relief="flat",
                padx=20,
                pady=8,
                cursor="hand2",
                command=dialog.destroy).pack(side="left", padx=5)
    

    def mostrar_nota_pendiente(self, alerta):
        """Muestra la nota de una falla pendiente"""
        if "nota_pendiente" not in alerta:
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Nota de Falla Pendiente")
        dialog.geometry("500x400")
        dialog.configure(bg=COLORES["fondo"])
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (500 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (400 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        tk.Label(dialog,
                text="📋 Detalle de Falla Pendiente",
                bg=COLORES["fondo"],
                fg=COLORES["texto"],
                font=("Segoe UI", 16, "bold")).pack(pady=20)
        
        info_frame = tk.Frame(dialog, bg=COLORES["card"])
        info_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(info_frame,
                text=f"Máquina: {alerta['maquina']}",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=10, pady=5)
        
        tk.Label(info_frame,
                text=f"Tipo: {alerta['tipo']}",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 11)).pack(anchor="w", padx=10, pady=5)
        
        if "fecha_pendiente" in alerta:
            tk.Label(info_frame,
                    text=f"Fecha: {alerta['fecha_pendiente']}",
                    bg=COLORES["card"],
                    fg=COLORES["texto_secundario"],
                    font=("Segoe UI", 10)).pack(anchor="w", padx=10, pady=5)
        
        tk.Label(dialog,
                text="Nota:",
                bg=COLORES["fondo"],
                fg=COLORES["texto"],
                font=("Segoe UI", 11, "bold")).pack(pady=(20, 5))
        
        texto_nota = tk.Text(dialog,
                            height=10,
                            width=50,
                            bg="#2d3047",
                            fg=COLORES["texto"],
                            font=("Segoe UI", 10),
                            wrap="word")
        texto_nota.pack(padx=20, pady=5)
        
        # CORREGIDO: Usar "1.0" con comillas
        texto_nota.insert("1.0", alerta["nota_pendiente"])
        texto_nota.config(state="disabled")
        
        btn_frame = tk.Frame(dialog, bg=COLORES["fondo"])
        btn_frame.pack(pady=20)
        
        def resolver_falla():
            respuesta = messagebox.askyesno(
                "Confirmar",
                "¿La falla ha sido resuelta?\n\n"
                "Se marcará como finalizada y se eliminará de la lista de pendientes.",
                parent=dialog
            )
            if respuesta:
                ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if "proceso" not in alerta:
                    alerta["proceso"] = ahora
                alerta["fin"] = ahora
                alerta["estado"] = "resuelta"
                
                guardar_falla(alerta, self.db_config)
                
                if alerta in self.fallas_activas:
                    self.fallas_activas.remove(alerta)
                
                guardar_fallas_activas(self.fallas_activas, self.db_config)
                
                self.actualizar_tabla()
                self.update_stats()
                
                if self.ventana_proyeccion and self.frame_tabla_proyeccion:
                    self.actualizar_tabla_proyeccion()
                
                dialog.destroy()
                messagebox.showinfo("✅ Completado", "Falla resuelta y registrada.")
        
        def editar_nota():
            dialog.destroy()
            self.mostrar_dialogo_nota_pendiente(alerta)
        
        tk.Button(btn_frame,
                text="✅ Marcar como Resuelta",
                bg=COLORES["success"],
                fg=COLORES["texto"],
                font=("Segoe UI", 10, "bold"),
                relief="flat",
                padx=15,
                pady=8,
                cursor="hand2",
                command=resolver_falla).pack(side="left", padx=5)
        
        tk.Button(btn_frame,
                text="✏️ Editar Nota",
                bg=COLORES["warning"],
                fg=COLORES["negro"],
                font=("Segoe UI", 10),
                relief="flat",
                padx=15,
                pady=8,
                cursor="hand2",
                command=editar_nota).pack(side="left", padx=5)
        
        tk.Button(btn_frame,
                text="❌ Cerrar",
                bg=COLORES["danger"],
                fg=COLORES["texto"],
                font=("Segoe UI", 10),
                relief="flat",
                padx=15,
                pady=8,
                cursor="hand2",
                command=dialog.destroy).pack(side="left", padx=5)

    def ver_fallas_pendientes(self):
        """Muestra una ventana con todas las fallas pendientes"""
        if not self.puede_ver_pendientes:
            messagebox.showinfo("Acceso Restringido",
                            "La vista de fallas pendientes está disponible\n"
                            "solo en licencias MID y PRO.",
                            parent=self.root)
            return
    
        pendientes = [a for a in self.fallas_activas if a.get("estado") == "pendiente"]
        
        if not pendientes:
            messagebox.showinfo("Información", 
                            "No hay fallas pendientes en este momento.")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Fallas Pendientes")
        dialog.geometry("900x600")
        dialog.configure(bg=COLORES["fondo"])
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (900 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (600 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Header
        header_frame = tk.Frame(dialog, bg=COLORES["card"])
        header_frame.pack(fill="x", padx=20, pady=20)
        
        tk.Label(header_frame,
                text=f"📋 Fallas Pendientes ({len(pendientes)})",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=20, pady=10)
        
        # Crear tabla
        columns = ("#", "Máquina", "Tipo", "Inicio", "Fecha Pendiente", "Nota")
        tree_frame = tk.Frame(dialog, bg=COLORES["fondo"])
        tree_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        # Configurar columnas
        tree.heading("#", text="#")
        tree.heading("Máquina", text="Máquina")
        tree.heading("Tipo", text="Tipo")
        tree.heading("Inicio", text="Inicio")
        tree.heading("Fecha Pendiente", text="Fecha Pendiente")
        tree.heading("Nota", text="Nota")
        
        tree.column("#", width=50, anchor="center")
        tree.column("Máquina", width=80, anchor="center")
        tree.column("Tipo", width=120, anchor="center")
        tree.column("Inicio", width=150, anchor="center")
        tree.column("Fecha Pendiente", width=150, anchor="center")
        tree.column("Nota", width=300, anchor="w")
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Insertar datos
        for alerta in pendientes:
            # DEBUG: Imprimir para verificar datos
            print(f"Insertando pendiente: {alerta}")
            
            # Formatear fechas
            inicio = alerta.get("inicio", "")
            if inicio and len(inicio) > 10:
                inicio = inicio[11:16]  # HH:MM
            
            fecha_pendiente = alerta.get("fecha_pendiente", "")
            if fecha_pendiente and len(fecha_pendiente) > 10:
                fecha_pendiente = fecha_pendiente[11:16]  # HH:MM
            
            nota = alerta.get("nota_pendiente", "")
            if len(nota) > 50:
                nota = nota[:50] + "..."
            
            valores = (
                f"#{alerta.get('numero_falla', '?')}",
                alerta["maquina"],
                alerta["tipo"],
                inicio,
                fecha_pendiente,
                nota
            )
            tree.insert("", "end", values=valores, tags=("pendiente",))
        
        tree.tag_configure("pendiente", background=COLORES.get("pendiente", "#FFA500"))
        
        # Bind para doble click
        tree.bind("<Double-1>", lambda e: self.mostrar_nota_desde_tree(e, tree, pendientes, dialog))
        
        # Botones de acción
        btn_frame = tk.Frame(dialog, bg=COLORES["fondo"])
        btn_frame.pack(fill="x", padx=20, pady=20)
        
        tk.Button(btn_frame,
                text="✅ Marcar Seleccionada como Resuelta",
                bg=COLORES["success"],
                fg=COLORES["texto"],
                font=("Segoe UI", 11),
                relief="flat",
                padx=15,
                pady=8,
                cursor="hand2",
                command=lambda: self.resolver_pendiente_seleccionada(tree, pendientes, dialog)).pack(side="left", padx=5)
        
        tk.Button(btn_frame,
                text="❌ Cerrar",
                bg=COLORES["danger"],
                fg=COLORES["texto"],
                font=("Segoe UI", 11),
                relief="flat",
                padx=15,
                pady=8,
                cursor="hand2",
                command=dialog.destroy).pack(side="right", padx=5)
    
    def resolver_pendiente_seleccionada(self, tree, pendientes, dialog):
        """Resuelve la falla pendiente seleccionada"""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Seleccionar", "Por favor selecciona una falla pendiente.", parent=dialog)
            return
        
        item = selection[0]
        values = tree.item(item, "values")
        
        # Buscar la falla
        for alerta in pendientes:
            if f"#{alerta.get('numero_falla', '?')}" == values[0] and alerta["maquina"] == values[1]:
                self.resolver_falla_pendiente(alerta, dialog)
                dialog.destroy()
                break
        
    def mostrar_nota_desde_tree(self, event, tree, pendientes, dialog):
        """Muestra la nota completa de una falla pendiente seleccionada"""
        selection = tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = tree.item(item, "values")
        
        # Buscar la falla correspondiente
        for alerta in pendientes:
            if f"#{alerta.get('numero_falla', '?')}" == values[0] and alerta["maquina"] == values[1]:
                self.mostrar_nota_pendiente(alerta)
                break

    def resolver_falla_pendiente(self, alerta, dialog=None):
        """Resuelve una falla pendiente - CORREGIDO: usa estado"""
        respuesta = messagebox.askyesno(
            "Confirmar",
            f"¿La falla de máquina {alerta['maquina']} - {alerta['tipo']} ha sido resuelta?",
            parent=dialog if dialog else self.root
        )

        if respuesta:
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Si no tiene proceso, asignarlo
            if "proceso" not in alerta or not alerta["proceso"]:
                alerta["proceso"] = ahora
            
            alerta["fin"] = ahora
            alerta["estado"] = "resuelta"

            guardar_falla(alerta, self.db_config)

            # Buscar por identificador único
            falla_a_eliminar = None
            for i, a in enumerate(self.fallas_activas):
                if a.get('numero_falla') == alerta.get('numero_falla') and a['maquina'] == alerta['maquina']:
                    falla_a_eliminar = a
                    break

            if falla_a_eliminar:
                self.fallas_activas.remove(falla_a_eliminar)
                print(f"✅ Falla pendiente #{alerta.get('numero_falla', '')} resuelta.")
            else:
                if alerta in self.fallas_activas:
                    self.fallas_activas.remove(alerta)

            guardar_fallas_activas(self.fallas_activas, self.db_config)

            self.actualizar_tabla()
            self.update_stats()

            if self.ventana_proyeccion and self.frame_tabla_proyeccion:
                self.actualizar_tabla_proyeccion()

            if dialog:
                dialog.destroy()

            messagebox.showinfo("✅ Completado", "Falla resuelta y registrada.")
        
    #===========================layout======================================

    def create_main_layout(self):
        self.sidebar = ModernFrame(self.root, width=250)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        header_frame = tk.Frame(self.sidebar, bg=COLORES["sidebar"], height=80)
        header_frame.pack(fill="x", pady=(0, 20))
        header_frame.pack_propagate(False)

        self.logo_label = tk.Label(header_frame,
                                  text=f"⚙️ {self.nombre_sistema}",
                                  bg=COLORES["sidebar"],
                                  fg=COLORES["texto"],
                                  font=("Segoe UI", 16, "bold"))
        self.logo_label.pack(pady=25)

        nav_buttons = [
            ("📊 Andon en Vivo", self.show_principal_view),
            ("📋 Historial", self.show_historial_view),
            ("📺 Proyección", self.toggle_proyeccion),
            ("⚙️ Configuración", self.mostrar_configuracion),
            ("📈 Estadísticas", self.mostrar_estadisticas),
            ("🤖 Generar Código ESP32", self.generar_codigo_esp32),
            ("🔐 Licencia", self.mostrar_menu_licencia)
        ]

        for text, command in nav_buttons:
            btn = tk.Button(self.sidebar,
                          text=text,
                          command=command,
                          bg=COLORES["sidebar"],
                          fg=COLORES["texto_secundario"],
                          font=("Segoe UI", 11),
                          relief="flat",
                          anchor="w",
                          padx=20,
                          pady=15,
                          cursor="hand2")
            btn.pack(fill="x")
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=COLORES["accento"], fg=COLORES["texto"]))
            btn.bind("<Leave>", lambda e, b=btn, t=text: b.config(bg=COLORES["sidebar"], fg=COLORES["texto_secundario"]) if b["text"] != "📊 Andon en Vivo" else None)

        self.main_content = ModernFrame(self.root)
        self.main_content.pack(side="right", fill="both", expand=True)

        self.header_frame = tk.Frame(self.main_content, bg=COLORES["card"], height=70)
        self.header_frame.pack(fill="x", padx=20, pady=(20, 10))
        self.header_frame.pack_propagate(False)

        self.header_label = tk.Label(self.header_frame,
                                    text="Panel de Control Andon",
                                    bg=COLORES["card"],
                                    fg=COLORES["texto"],
                                    font=("Segoe UI", 18, "bold"))
        self.header_label.pack(side="left", padx=30)

        self.status_frame = tk.Frame(self.header_frame, bg=COLORES["card"])
        self.status_frame.pack(side="right", padx=30)

        self.status_indicator = tk.Label(self.status_frame,
                                        text="●",
                                        bg="#4CAF50",
                                        fg="#4CAF50",
                                        font=("Arial", 14))
        self.status_indicator.pack(side="left")

        self.status_label = tk.Label(self.status_frame,
                                    text="Sistema Activo",
                                    bg=COLORES["card"],
                                    fg=COLORES["texto_secundario"],
                                    font=("Segoe UI", 10))
        self.status_label.pack(side="left", padx=5)

        self.content_area = ModernFrame(self.main_content)
        self.content_area.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.setup_principal()
        self.setup_historial()
        

    def show_principal_view(self):
        self.header_label.config(text="Panel de Control Andon")
        self.frame_historial.pack_forget()
        self.frame_principal.pack(fill="both", expand=True)

    def show_historial_view(self):
        self.header_label.config(text="Historial de Fallas")
        self.frame_principal.pack_forget()
        self.frame_historial.pack(fill="both", expand=True)

    def setup_principal(self):
        self.frame_principal = ModernFrame(self.content_area)

        quick_input_frame = tk.Frame(self.frame_principal, bg=COLORES["card"])
        quick_input_frame.pack(fill="x", padx=20, pady=20)

        tk.Label(quick_input_frame,
                text="Registro Rápido",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 15))

        input_row = tk.Frame(quick_input_frame, bg=COLORES["card"])
        input_row.pack(fill="x")

        tk.Label(input_row,
                text="Máquina:",
                bg=COLORES["card"],
                fg=COLORES["texto_secundario"],
                font=("Segoe UI", 10)).pack(side="left", padx=(0, 10))

        self.entrada_maquina = ModernCombobox(input_row, values=MAQUINAS, width=15)
        self.entrada_maquina.pack(side="left", padx=(0, 30))

        self.tipos_frame = tk.Frame(input_row, bg=COLORES["card"])
        self.tipos_frame.pack(side="left", padx=10)

        self.actualizar_botones_tipos()

        stats_frame = tk.Frame(self.frame_principal, bg=COLORES["card"])
        stats_frame.pack(fill="x", padx=20, pady=(0, 20))

        button_row = tk.Frame(stats_frame, bg=COLORES["card"])
        button_row.pack(fill="x", padx=20, pady=(10, 5))

        tk.Label(button_row,
                text="Estadísticas en Tiempo Real",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 12, "bold")).pack(side="left")
        
        
        # ===== BOTONES SIEMPRE VISIBLES (empaquetar de derecha a izquierda) =====
        # Botón cerrar todas las fallas (siempre visible)
        tk.Button(button_row,
                text="🔴 CERRAR TODAS",
                bg=COLORES["danger"],
                fg=COLORES["texto"],
                font=("Segoe UI", 9, "bold"),
                relief="flat",
                padx=8,
                pady=3,
                cursor="hand2",
                command=self.cerrar_todas_fallas_activas).pack(side="right", padx=2)
        
        # Botón para actualizar desde BD (siempre visible)
        tk.Button(button_row,
                text="🔄 ACTUALIZAR BD",
                bg=COLORES["success"],
                fg=COLORES["texto"],
                font=("Segoe UI", 9, "bold"),
                relief="flat",
                padx=8,
                pady=3,
                cursor="hand2",
                command=self.actualizar_desde_bd).pack(side="right", padx=2)
        
        # ===== BOTONES PARA PENDIENTES =====
        # Nota: Estos botones se crearán después de aplicar los límites de licencia
        # por eso los guardamos como variables para mostrarlos después
        self.pendientes_btn_frame = tk.Frame(button_row, bg=COLORES["card"])
        #self.pendientes_btn_frame.pack(side="right", padx=2)
        
        # Inicialmente ocultos, se mostrarán después de aplicar límites
        self.pendientes_btn_frame.pack_forget()

        self.stats_container = tk.Frame(stats_frame, bg=COLORES["card"])
        self.stats_container.pack(fill="x", padx=20, pady=(5, 15))

        counter_frame = tk.Frame(stats_frame, bg=COLORES["card"])
        counter_frame.pack(fill="x", padx=20, pady=(0, 15))

        self.contador_fallas = tk.Label(counter_frame,
                                        text="0 activas",
                                        bg=COLORES["accento"],
                                        fg=COLORES["texto"],
                                        font=("Segoe UI", 10, "bold"),
                                        padx=15,
                                        pady=5)
        self.contador_fallas.pack(side="left")

        self.update_stats()

        tabla_container = tk.Frame(self.frame_principal, bg=COLORES["fondo"])
        tabla_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        tk.Label(tabla_container,
                text="Fallas Activas",
                bg=COLORES["fondo"],
                fg=COLORES["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 10))

        self.frame_tabla = ModernFrame(tabla_container)
        self.frame_tabla.pack(fill="both", expand=True)
    
    def actualizar_botones_tipos(self):
        for widget in self.tipos_frame.winfo_children():
            widget.destroy()

        for tipo in self.tipos_falla:
            color = self.get_color_for_tipo(tipo)
            btn = tk.Button(self.tipos_frame,
                        text=tipo,
                        command=lambda t=tipo: self.registrar_evento_manual(t),
                        bg=color,
                        fg=self.get_text_color_for_background(color),
                        font=("Segoe UI", 9, "bold"),
                        relief="flat",
                        padx=15,
                        pady=8,
                        cursor="hand2")
            btn.pack(side="left", padx=5)
            btn.bind("<Enter>", lambda e, b=btn, c=color: b.config(bg=self.lighten_color(c, 0.1)))
            btn.bind("<Leave>", lambda e, b=btn, c=color: b.config(bg=c))

    def setup_historial(self):
        self.frame_historial = ModernFrame(self.content_area)

        filters_card = tk.Frame(self.frame_historial, bg=COLORES["card"])
        filters_card.pack(fill="x", padx=20, pady=20)

        tk.Label(filters_card,
                text="Filtrar Historial",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=20, pady=(15, 10))

        filters_grid = tk.Frame(filters_card, bg=COLORES["card"])
        filters_grid.pack(fill="x", padx=20, pady=(0, 20))

        row1 = tk.Frame(filters_grid, bg=COLORES["card"])
        row1.pack(fill="x", pady=5)

        tk.Label(row1,
                text="Máquina:",
                bg=COLORES["card"],
                fg=COLORES["texto_secundario"],
                font=("Segoe UI", 10)).grid(row=0, column=0, padx=(0, 10))

        self.filtro_maquina = ModernEntry(row1, width=15)
        self.filtro_maquina.grid(row=0, column=1, padx=(0, 30))

        tk.Label(row1,
                text="Tipo:",
                bg=COLORES["card"],
                fg=COLORES["texto_secundario"],
                font=("Segoe UI", 10)).grid(row=0, column=2, padx=(0, 10))

        self.filtro_tipo = ModernCombobox(row1, values=[""] + self.tipos_falla, width=15)
        self.filtro_tipo.grid(row=0, column=3, padx=(0, 30))

        row2 = tk.Frame(filters_grid, bg=COLORES["card"])
        row2.pack(fill="x", pady=5)

        tk.Label(row2,
                text="Desde:",
                bg=COLORES["card"],
                fg=COLORES["texto_secundario"],
                font=("Segoe UI", 10)).grid(row=0, column=0, padx=(0, 10))

        self.filtro_desde = DateEntry(row2, date_pattern='yyyy-mm-dd', width=15)
        self.filtro_desde.grid(row=0, column=1, padx=(0, 30))

        tk.Label(row2,
                text="Hasta:",
                bg=COLORES["card"],
                fg=COLORES["texto_secundario"],
                font=("Segoe UI", 10)).grid(row=0, column=2, padx=(0, 10))

        self.filtro_hasta = DateEntry(row2, date_pattern='yyyy-mm-dd', width=15)
        self.filtro_hasta.grid(row=0, column=3, padx=(0, 30))
        
        # Filtro de estado MEJORADO
        estado_frame = tk.Frame(filters_grid, bg=COLORES["card"])
        estado_frame.pack(fill="x", pady=5)

        tk.Label(estado_frame,
                text="Estado:",
                bg=COLORES["card"],
                fg=COLORES["texto_secundario"],
                font=("Segoe UI", 10)).pack(side="left", padx=(0, 10))

        # Ahora incluye la opción "Fue Pendiente"
        opciones_estado = ["", "Resuelta", "Fue Pendiente"]
        self.filtro_estado = ModernCombobox(estado_frame, 
                                        values=opciones_estado, 
                                        width=15)
        self.filtro_estado.pack(side="left", padx=(0, 30))

        action_frame = tk.Frame(filters_card, bg=COLORES["card"])
        action_frame.pack(fill="x", padx=20, pady=(0, 20))

        ModernButton(action_frame,
                    text="🔍 Buscar",
                    command=self.cargar_historial).pack(side="left", padx=5)
        ModernButton(action_frame,
                    text="📊 Ver Gráficas",
                    command=self.mostrar_todas_graficas).pack(side="left", padx=5)
        ModernButton(action_frame,
                    text="📁 Exportar Excel",
                    command=self.exportar_excel_completo).pack(side="left", padx=5)

        table_container = tk.Frame(self.frame_historial, bg=COLORES["fondo"])
        table_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.frame_historial_tabla = ModernFrame(table_container)
        self.frame_historial_tabla.pack(fill="both", expand=True)

    def lighten_color(self, color, factor=0.2):
        if isinstance(color, str) and color.startswith('#'):
            color = color.lstrip('#')
            rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        else:
            rgb = color
        h, l, s = rgb_to_hls(rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0)
        l = min(1.0, l + factor)
        r, g, b = hls_to_rgb(h, l, s)
        return f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'

    def update_stats(self):
        # Verificar que la ventana principal existe
        if not self.root or not self.root.winfo_exists():
            return
            
        for widget in self.stats_container.winfo_children():
            widget.destroy()

        activas = len(self.fallas_activas)
        en_proceso = sum(1 for a in self.fallas_activas if "proceso" in a and "fin" not in a)

        tiempo_promedio = self.get_tiempo_promedio()
        tiempo_min = tiempo_promedio / 60 if tiempo_promedio else 0

        resueltas_hoy = self.get_resueltas_hoy()

        stats = {
            "Fallas Activas": activas,
            "En Proceso": en_proceso,
            "Resueltas Hoy": resueltas_hoy,
            "Tiempo Promedio (min)": f"{tiempo_min:.1f}"
        }

        for label, value in stats.items():
            stat_card = tk.Frame(
                self.stats_container,
                bg=self.lighten_color(COLORES["card"], -0.1),
                relief="flat",
                borderwidth=1,
                highlightbackground=COLORES["texto_secundario"]
            )
            stat_card.pack(side="left", fill="both", expand=True, padx=5)

            tk.Label(
                stat_card,
                text=str(value),
                bg=self.lighten_color(COLORES["card"], -0.1),
                fg=COLORES["texto"],
                font=("Segoe UI", 18, "bold")
            ).pack(pady=(15, 5))

            tk.Label(
                stat_card,
                text=label,
                bg=self.lighten_color(COLORES["card"], -0.1),
                fg=COLORES["texto_secundario"],
                font=("Segoe UI", 9)
            ).pack(pady=(0, 15))

        # ✅ Verificar que el contador_fallas existe antes de configurarlo
        if hasattr(self, 'contador_fallas') and self.contador_fallas and self.contador_fallas.winfo_exists():
            self.contador_fallas.config(text=f"{activas} activas")

        # ✅ Verificar que proj_counter existe antes de configurarlo
        if hasattr(self, 'proj_counter') and self.proj_counter and self.proj_counter.winfo_exists():
            self.proj_counter.config(text=str(activas))

        self.root.update_idletasks()

        print(f"📊 Estadísticas actualizadas - Activas: {activas}, En proceso: {en_proceso}")
    
    def get_resueltas_hoy(self):
        """Obtiene el número de fallas resueltas hoy desde MySQL"""
        if not self.mysql_disponible:
            return 0
        
        hoy = datetime.now().strftime("%Y-%m-%d")
        conn = self._conectar_mysql()
        if not conn:
            return 0
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM fallas WHERE DATE(fin) = %s", (hoy,))
            count = cursor.fetchone()[0] or 0
            cursor.close()
            conn.close()
            return count
        except Exception as e:
            print(f"Error obteniendo resueltas hoy: {e}")
            return 0

    def get_tiempo_promedio(self):
        """Obtiene el tiempo promedio de resolución desde MySQL"""
        if not self.mysql_disponible:
            return 0
        
        conn = self._conectar_mysql()
        if not conn:
            return 0
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT AVG(TIMESTAMPDIFF(SECOND, inicio, fin))
                FROM fallas
                WHERE fin IS NOT NULL
            """)
            resultado = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            
            if resultado is not None:
                return float(resultado)
            return 0
        except Exception as e:
            print(f"Error obteniendo tiempo promedio: {e}")
            return 0
    
    def iniciar_lectura_red(self):
        """Servidor TCP con pool de hilos y cola de eventos"""
        
        # Cola de eventos con límite para evitar desbordamiento
        self.event_queue = queue.Queue(maxsize=10000)
        self.event_processor_running = True
        
        def procesar_cola_eventos():
            """Procesa eventos en lote cada 100ms"""
            batch = []
            last_process = time.time()
            
            while self.event_processor_running:
                try:
                    # Obtener evento con timeout
                    evento = self.event_queue.get(timeout=0.1)
                    batch.append(evento)
                    
                    # Procesar cada 100ms o si el lote es grande
                    if len(batch) >= 10 or (time.time() - last_process) > 0.1:
                        self.root.after(0, lambda b=batch.copy(): self.procesar_batch_eventos(b))
                        batch.clear()
                        last_process = time.time()
                        
                except queue.Empty:
                    if batch:
                        self.root.after(0, lambda b=batch.copy(): self.procesar_batch_eventos(b))
                        batch.clear()
                        last_process = time.time()
                    continue
                except Exception as e:
                    print(f"Error procesando cola: {e}")
        
        def manejador_cliente(client_socket, addr):
            """Maneja una conexión de cliente individual"""
            try:
                client_socket.settimeout(5.0)  # Timeout de 5 segundos
                data = client_socket.recv(64).decode().strip()
                if data and '|' in data:
                    maquina, tipo = data.split('|', 1)
                    try:
                        self.event_queue.put_nowait((maquina.strip(), tipo.strip()))
                    except queue.Full:
                        print(f"⚠️ Cola llena, descartando evento de {addr}")
                client_socket.close()
            except socket.timeout:
                print(f"⏱️ Timeout en conexión de {addr}")
            except Exception as e:
                print(f"Error con cliente {addr}: {e}")
            finally:
                client_socket.close()
        
        def servidor_tcp():
            """Bucle principal del servidor TCP"""
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((HOST, PORT))
            server.listen(200)  # Cola de 200 conexiones
            print(f"🟢 Servidor Andon escuchando en {HOST}:{PORT} (máx 200 conexiones)")
            
            while True:
                try:
                    client, addr = server.accept()
                    # Hilo por cliente (rápido)
                    threading.Thread(target=manejador_cliente, 
                                    args=(client, addr), 
                                    daemon=True).start()
                except Exception as e:
                    print(f"Error en accept: {e}")
                    time.sleep(0.1)
        
        # Iniciar hilo del servidor
        threading.Thread(target=servidor_tcp, daemon=True).start()
        # Iniciar procesador de cola
        threading.Thread(target=procesar_cola_eventos, daemon=True).start()
    
    def procesar_batch_eventos(self, batch):
        """Procesa un lote de eventos en el hilo principal"""
        for maquina, tipo in batch:
            self.registrar_evento(maquina, tipo)
    
    def iniciar_lectura_serial(self):
        def buscar_puerto():
            for port in serial.tools.list_ports.comports():
                if "CP210" in port.description or "Silicon" in port.description:
                    return port.device
            return None
        def leer_serial():
            puerto = buscar_puerto()
            if not puerto:
                print("ESP32 no detectado")
                return
            try:
                with serial.Serial(puerto, 115200, timeout=1) as ser:
                    while True:
                        try:
                            linea = ser.readline().decode("utf-8").strip()
                        except Exception as e:
                            continue
                        if linea:
                            partes = linea.split("|")
                            if len(partes) != 2:
                                continue
                            maquina, tipo = partes
                            self.root.after(0, lambda: self.registrar_evento(maquina, tipo))
            except Exception as e:
                print("Error en lectura serial:", e)
        threading.Thread(target=leer_serial, daemon=True).start()

    def registrar_evento_manual(self, tipo):
        maquina = self.entrada_maquina.get().strip()
        if maquina:
            self.registrar_evento(maquina, tipo)

    def registrar_evento(self, maquina, identificador):
        """
        Registra un evento de falla.
        maquina: str (ej. "1")
        identificador: puede ser "Boton1" (desde ESP32) o "Mantenimiento" (desde interfaz manual)
        """
        
        print(f"🔍 DEBUG - registrar_evento llamado con: maquina='{maquina}', identificador='{identificador}'")
        
        # DEBUG: Ver exactamente qué está llegando
        print(f"🔍 DEBUG - registrar_evento llamado con: maquina='{maquina}', identificador='{identificador}'")
        print(f"🔍 DEBUG - tipo maquina: {type(maquina)}, tipo identificador: {type(identificador)}")
        print(f"🔍 DEBUG - repr(identificador): {repr(identificador)}")
        
        if not self.verificar_limite_maquina(maquina):
            return

        # ===== DETECTAR EL FORMATO DEL IDENTIFICADOR =====
        # ===== DETECTAR EL FORMATO DEL IDENTIFICADOR =====
        if identificador and identificador.startswith("Boton"):
            print(f"🔍 DEBUG - Detectado formato Boton")
            try:
                # Limpiar el identificador de posibles caracteres extra
                limpio = identificador.strip()
                numero_boton = int(limpio.replace("Boton", ""))
                print(f"🔍 DEBUG - Botón extraído: {numero_boton}")
                
                tipo_falla = self.mapeo_botones.get(numero_boton)
                if tipo_falla is None:
                    print(f"⚠️ Botón {numero_boton} no está mapeado a ninguna falla")
                    print(f"🔍 DEBUG - Mapeo actual: {self.mapeo_botones}")
                    self.root.after(0, lambda: messagebox.showwarning(
                        "Mapeo Faltante",
                        f"Botón {numero_boton} (Máquina {maquina}) no está configurado.\n"
                        "Ve a Configuración para asignarle un tipo de falla."
                    ))
                    return
                print(f"🔍 DEBUG - Tipo de falla mapeado: {tipo_falla}")
            except Exception as e:
                print(f"❌ Error procesando botón: {e}")
                print(f"❌ Identificador problemático: {repr(identificador)}")
                return
        else:
            # Es un nombre de tipo de falla desde la interfaz manual
            print(f"🔍 DEBUG - Detectado formato manual")
            tipo_falla = identificador
            # Verificar que el tipo exista
            if tipo_falla not in self.tipos_falla:
                print(f"⚠️ Tipo de falla '{tipo_falla}' no válido")
                return
            numero_boton = None

        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Buscar si ya existe una falla activa para esta máquina y tipo
        falla_encontrada = None
        for alerta in self.fallas_activas:
            if alerta["maquina"] == maquina and alerta["tipo"] == tipo_falla:
                falla_encontrada = alerta
                break
        
        # ... (resto del código igual, usando tipo_falla) ...
        if falla_encontrada:
            # DEBUG: Ver qué estamos recibiendo
            print(f"🔍 Falla encontrada: Estado={falla_encontrada.get('estado')}")
            
            estado_actual = falla_encontrada.get("estado", "activa")
            
            # CASO 1: Estado pendiente - no se puede modificar con clic simple
            if estado_actual == "pendiente":
                messagebox.showinfo("Falla Pendiente", 
                                "Esta falla está marcada como pendiente.\n"
                                "Usa doble clic para ver detalles o resolverla.",
                                parent=self.root)
                return
            
            # CASO 2: Estado activa - primer clic (pasar a en_proceso)
            elif estado_actual == "activa":
                falla_encontrada["proceso"] = ahora
                falla_encontrada["estado"] = "en_proceso"
                print(f"✅ Falla en proceso: {maquina} - {tipo_falla} (Estado: en_proceso)")
                
                guardar_falla(falla_encontrada, self.db_config)
            
            # CASO 3: Estado en_proceso - segundo clic (finalizar)
            elif estado_actual == "en_proceso":
                falla_encontrada["fin"] = ahora
                falla_encontrada["estado"] = "resuelta"
                print(f"✅ Falla finalizada: {maquina} - {tipo_falla} (Estado: resuelta)")
                
                guardar_falla(falla_encontrada, self.db_config)
                
                # Eliminar de fallas activas
                self.fallas_activas.remove(falla_encontrada)
                if id(falla_encontrada) in self.numeros_falla_asignados:
                    del self.numeros_falla_asignados[id(falla_encontrada)]
            
            # CASO 4: Estado resuelta - no debería pasar, pero por si acaso
            elif estado_actual == "resuelta":
                print(f"⚠️ Falla ya resuelta, no se puede modificar")
                if falla_encontrada in self.fallas_activas:
                    self.fallas_activas.remove(falla_encontrada)
                    guardar_fallas_activas(self.fallas_activas, self.db_config)
            
            else:
                print(f"❌ Estado no manejado: {estado_actual}")
                return
            
            # Actualizar interfaz
            self.actualizar_tabla()
            if self.root and self.root.winfo_exists():
                self.update_stats()
            
            guardar_fallas_activas(self.fallas_activas, self.db_config)
            
            if self.ventana_proyeccion and self.frame_tabla_proyeccion:
                self.actualizar_tabla_proyeccion()
                
        else:
            # CASO 5: Nueva falla
            numero_falla = self.obtener_siguiente_numero_falla()
            print(f"🆕 Nueva falla #{numero_falla}: {maquina} - {tipo_falla}" + 
                (f" (Botón {numero_boton})" if numero_boton else " (Manual)"))

            nueva_falla = {
                "maquina": maquina,
                "tipo": tipo_falla,
                "inicio": ahora,
                "numero_falla": numero_falla,
                "estado": "activa"
            }

            guardar_falla(nueva_falla, self.db_config)

            self.fallas_activas.append(nueva_falla)
            self.numeros_falla_asignados[id(nueva_falla)] = numero_falla

            self.actualizar_tabla()
            self.update_stats()
            self.reproducir_alarma()

            guardar_fallas_activas(self.fallas_activas, self.db_config)

            if self.ventana_proyeccion and self.frame_tabla_proyeccion:
                self.actualizar_tabla_proyeccion()
            
    def obtener_siguiente_numero_falla(self):
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
        config["ultimo_numero_usado"] = config["consecutivo_actual"]
        guardar_config_contador(config, self.db_config)

        return config["consecutivo_actual"]

    def reproducir_alarma(self):
        threading.Thread(target=lambda: winsound.Beep(1500, 1000)).start()

    #============Actualizar tabla fallas=====================
    
    def _crear_tabla_principal(self):
        """Crea la tabla principal por primera vez y la configura"""
        # Limpiar el frame
        for widget in self.frame_tabla.winfo_children():
            widget.destroy()
        
        # Crear frame contenedor para la tabla
        tree_frame = ModernFrame(self.frame_tabla)
        tree_frame.pack(fill="both", expand=True)
        
        # Definir columnas
        columnas = ("#", "Máquina", "Tipo", "Inicio", "Proceso", "Fin", "Estado", "Nota")
        anchos = [60, 100, 120, 100, 100, 100, 100, 80]
        
        # Crear Treeview
        self.treeview_principal = ttk.Treeview(
            tree_frame, 
            columns=columnas, 
            show="headings", 
            style="Treeview"
        )
        
        # Configurar columnas
        for col, ancho in zip(columnas, anchos):
            self.treeview_principal.heading(col, text=col)
            self.treeview_principal.column(col, width=ancho, anchor="center")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.treeview_principal.yview)
        self.treeview_principal.configure(yscrollcommand=scrollbar.set)
        
        # Posicionar
        self.treeview_principal.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Diccionario para almacenar los datos asociados a cada item
        self.treeview_principal.item_data = {}
        
        # Bind para doble click
        self.treeview_principal.bind("<Double-1>", self._on_treeview_double_click)
        
        # Llenar con datos iniciales
        self._refrescar_tabla_completa()

    def _refrescar_tabla_completa(self):
        """Llena la tabla con todas las fallas activas"""
        # Limpiar datos existentes
        for item in self.treeview_principal.get_children():
            self.treeview_principal.delete(item)
        
        self.treeview_principal.item_data.clear()
        
        # Aplicar filtro de ocultar pendientes si está activo
        fallas_a_mostrar = self.fallas_activas
        if hasattr(self, 'ocultar_pendientes_var') and self.ocultar_pendientes_var.get():
            fallas_a_mostrar = [a for a in self.fallas_activas if a.get("estado") != "pendiente"]
        
        if not fallas_a_mostrar:
            return
        
        # Configurar tags de color para cada tipo
        tipos_unicos = set([alerta["tipo"] for alerta in fallas_a_mostrar])
        for tipo in tipos_unicos:
            color = self.get_color_for_tipo(tipo)
            self.treeview_principal.tag_configure(
                tipo,
                background=color,
                foreground=self.get_text_color_for_background(color),
                font=("Segoe UI", 10, "bold")
            )
        
        # Configurar tag para pendientes
        self.treeview_principal.tag_configure(
            "pendiente", 
            background=COLORES.get("pendiente", "#FFA500")
        )
        
        # Insertar datos
        for idx, alerta in enumerate(fallas_a_mostrar, 1):
            valores = self._get_falla_values(alerta, idx)
            
            # Determinar tags
            tags = [alerta["tipo"]]
            if alerta.get("estado") == "pendiente":
                tags.append("pendiente")
            
            # Insertar y guardar referencia
            item_id = self.treeview_principal.insert("", "end", values=valores, tags=tags)
            self.treeview_principal.item_data[item_id] = alerta

    def _on_treeview_double_click(self, event):
        """Maneja el doble click en la tabla"""
        try:
            item = self.treeview_principal.selection()[0]
            alerta = self.treeview_principal.item_data.get(item)
            if alerta:
                self.on_doble_click_falla(event, alerta)
        except IndexError:
            pass
        except Exception as e:
            print(f"Error en doble click: {e}")
            
    def _get_falla_values(self, alerta, idx=None):
        """Obtiene los valores formateados de una falla para la tabla"""
        numero = alerta.get("numero_falla", idx if idx else "?")
        
        # Usar el estado guardado directamente
        estado_guardado = alerta.get("estado", "activa")
        
        # Determinar el texto a mostrar basado en el estado guardado
        if estado_guardado == "pendiente":
            estado = "🟠 Pendiente"
        elif estado_guardado == "en_proceso":
            estado = "🟡 En Proceso"
        elif estado_guardado == "resuelta":
            estado = "✅ Resuelta"
        else:  # "activa" o cualquier otro
            estado = "🔴 Activa"
        
        # Indicador de nota
        tiene_nota = "📝" if "nota_pendiente" in alerta and alerta["nota_pendiente"] else ""
        
        # Función para extraer solo la hora
        def solo_hora(fecha_completa):
            if not fecha_completa:
                return ""
            try:
                # Si ya es solo hora, devolverla
                if len(fecha_completa) <= 8 and ":" in fecha_completa:
                    return fecha_completa
                # Si es fecha completa, extraer hora
                return datetime.strptime(fecha_completa, "%Y-%m-%d %H:%M:%S").strftime("%H:%M:%S")
            except:
                return fecha_completa if fecha_completa else ""
        
        return (
            f"#{numero}",
            alerta["maquina"],
            alerta["tipo"],
            solo_hora(alerta.get("inicio", "")),
            solo_hora(alerta.get("proceso", "")),
            solo_hora(alerta.get("fin", "")),
            estado,
            tiene_nota
        )

    def actualizar_tabla(self):
        """Versión optimizada: actualiza solo filas modificadas"""
        # Si la tabla no existe aún, crearla
        if not hasattr(self, 'treeview_principal') or not self.treeview_principal.winfo_exists():
            self._crear_tabla_principal()
            return
        
        # Determinar qué fallas mostrar
        fallas_a_mostrar = self.fallas_activas
        if hasattr(self, 'ocultar_pendientes_var') and self.ocultar_pendientes_var.get():
            fallas_a_mostrar = [a for a in self.fallas_activas if a.get("estado") != "pendiente"]
        
        # Actualizar contador
        if hasattr(self, 'contador_fallas'):
            self.contador_fallas.config(text=f"{len(fallas_a_mostrar)} activas")
        
        if not fallas_a_mostrar:
            # Si no hay fallas, limpiar tabla
            for item in self.treeview_principal.get_children():
                self.treeview_principal.delete(item)
            self.treeview_principal.item_data.clear()
            return
        
        # Obtener IDs actuales en la tabla
        ids_actuales = set()
        items_actuales = {}
        for child in self.treeview_principal.get_children():
            item = self.treeview_principal.item(child)
            item_id = item['values'][0] if item['values'] else None
            if item_id:
                ids_actuales.add(item_id)
                items_actuales[item_id] = child
        
        # Crear conjunto de IDs de las fallas activas
        ids_nuevos = set()
        fallas_por_id = {}
        
        for i, alerta in enumerate(fallas_a_mostrar, 1):
            num_id = f"#{alerta.get('numero_falla', i)}"
            ids_nuevos.add(num_id)
            fallas_por_id[num_id] = alerta
        
        # Eliminar los que ya no están
        for id_eliminar in ids_actuales - ids_nuevos:
            if id_eliminar in items_actuales:
                self.treeview_principal.delete(items_actuales[id_eliminar])
                # Limpiar del diccionario item_data
                items_a_eliminar = [k for k, v in self.treeview_principal.item_data.items() 
                                if v.get('numero_falla') == int(id_eliminar[1:])]
                for k in items_a_eliminar:
                    del self.treeview_principal.item_data[k]
        
        # Actualizar o insertar los que están
        for i, alerta in enumerate(fallas_a_mostrar, 1):
            num_id = f"#{alerta.get('numero_falla', i)}"
            valores = self._get_falla_values(alerta, i)
            
            # Determinar tags
            tags = [alerta["tipo"]]
            if alerta.get("estado") == "pendiente":
                tags.append("pendiente")
            
            if num_id in ids_actuales:
                # Actualizar fila existente
                item_id = items_actuales[num_id]
                self.treeview_principal.item(item_id, values=valores, tags=tags)
                self.treeview_principal.item_data[item_id] = alerta
            else:
                # Insertar nueva
                item_id = self.treeview_principal.insert("", "end", values=valores, tags=tags)
                self.treeview_principal.item_data[item_id] = alerta
        
        # Actualizar configuración de colores por si hay nuevos tipos
        tipos_unicos = set([alerta["tipo"] for alerta in fallas_a_mostrar])
        for tipo in tipos_unicos:
            color = self.get_color_for_tipo(tipo)
            self.treeview_principal.tag_configure(
                tipo,
                background=color,
                foreground=self.get_text_color_for_background(color),
                font=("Segoe UI", 10, "bold")
            )
   
    #==========================================
                
    def debug_fallas_cargadas(self):
        """Función de depuración para verificar las fallas cargadas"""
        print("\n=== DEBUG FALLAS CARGADAS ===")
        print(f"Total fallas: {len(self.fallas_activas)}")
        for i, falla in enumerate(self.fallas_activas):
            print(f"Falla {i+1}:")
            print(f"  Máquina: {falla.get('maquina')}")
            print(f"  Tipo: {falla.get('tipo')}")
            print(f"  Estado: {falla.get('estado')}")
            print(f"  Inicio: {falla.get('inicio')}")
        print("==============================\n")

    def toggle_ocultar_pendientes(self):
        """Alterna entre mostrar y ocultar fallas pendientes"""
        if not hasattr(self, 'ocultar_pendientes_var'):
            self.ocultar_pendientes_var = tk.BooleanVar(value=False)
        
        self.ocultar_pendientes_var.set(not self.ocultar_pendientes_var.get())
        
        # Actualizar texto del botón
        for widget in self.pendientes_btn_frame.winfo_children():
            if isinstance(widget, tk.Button) and widget["text"].startswith("👁️"):
                if self.ocultar_pendientes_var.get():
                    widget.config(text="👁️ MOSTRAR", bg=COLORES["success"])
                else:
                    widget.config(text="👁️ OCULTAR", bg=COLORES["card"])
        
        self.actualizar_tabla()
        
    #===============FINALIZAR FALLA MANUAL===========================
    def on_doble_click_falla(self, event, alerta):
        """Maneja el doble click en una falla de la tabla según licencia"""
        menu = tk.Menu(self.root, tearoff=0, bg=COLORES["card"], fg=COLORES["texto"])
        
        estado_actual = alerta.get("estado", "activa")
        print(f"🎯 Doble clic en falla: Estado={estado_actual}, Máq={alerta['maquina']}")

        # ===== OPCIÓN PARA VER NOTA SI EXISTE (SIEMPRE) =====
        tiene_nota = False
        if "nota_pendiente" in alerta and alerta["nota_pendiente"]:
            tiene_nota = True
            menu.add_command(label="📋 Ver Nota", 
                            command=lambda: self.mostrar_nota_pendiente(alerta))
        
        # ===== OPCIÓN PARA AGREGAR/EDITAR NOTA (SOLO PRO) =====
        if self.puede_agregar_notas:
            if tiene_nota:
                menu.add_command(label="✏️ Editar Nota", 
                                command=lambda: self.mostrar_dialogo_nota(alerta))
            else:
                menu.add_command(label="📝 Agregar Nota", 
                                command=lambda: self.mostrar_dialogo_nota(alerta))
        
        # ===== OPCIONES DE FLUJO (basadas en el estado) =====
        # Las opciones de flujo se muestran en el orden lógico
        
        # 1. Si está activa, la única opción es pasarla a proceso
        if estado_actual == "activa":
            if menu.index("end") is not None:
                menu.add_separator()
            menu.add_command(label="🟡 Marcar en Proceso", 
                            command=lambda: self.marcar_en_proceso(alerta))
            # [ELIMINADO] Ya no se permite finalizar desde activa
        
        # 2. Si está en proceso, se puede finalizar o (si aplica) marcar pendiente
        elif estado_actual == "en_proceso":
            if menu.index("end") is not None:
                menu.add_separator()
            
            # Opción para marcar pendiente (solo MID/PRO)
            if self.puede_usar_pendientes:
                menu.add_command(label="🟠 Marcar como Pendiente", 
                                command=lambda: self.mostrar_dialogo_nota_pendiente(alerta))
            
            # Opción para finalizar
            menu.add_command(label="✅ Finalizar Falla", 
                            command=lambda: self.finalizar_falla_manual(alerta))
        
        # 3. Si está pendiente, se puede finalizar (resolver)
        elif estado_actual == "pendiente":
            if menu.index("end") is not None:
                menu.add_separator()
            menu.add_command(label="✅ Resolver Pendiente (Finalizar)", 
                            command=lambda: self.finalizar_falla_manual(alerta))
            # [NOTA] La función finalizar_falla_manual ya maneja el caso de pendiente correctamente.
        
        # [ELIMINADO] El caso de "resuelta" no debería llegar aquí porque ya no está en fallas_activas.
        
        # Solo mostrar el menú si tiene opciones
        if menu.index("end") is not None:
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()
   
   #=================dialogo nota==================================
    def mostrar_dialogo_nota(self, alerta):
        """Muestra un diálogo para agregar/editar nota a cualquier falla (solo PRO)"""
        if not self.puede_agregar_notas:
            messagebox.showinfo("Acceso Restringido",
                            "Agregar notas solo está disponible\n"
                            "en licencias PRO.",
                            parent=self.root)
            return
            
        dialog = tk.Toplevel(self.root)
        dialog.title("Nota de Falla")
        dialog.geometry("500x450")
        dialog.configure(bg=COLORES["fondo"])
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (500 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (450 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Título
        tk.Label(dialog,
                text="📝 Agregar/Editar Nota",
                bg=COLORES["fondo"],
                fg=COLORES["texto"],
                font=("Segoe UI", 16, "bold")).pack(pady=20)
        
        # Información de la falla
        info_frame = tk.Frame(dialog, bg=COLORES["card"])
        info_frame.pack(fill="x", padx=20, pady=10)
        
        estado_text = ""
        if alerta.get("estado") == "pendiente":
            estado_text = " (Pendiente)"
        
        tk.Label(info_frame,
                text=f"Máquina: {alerta['maquina']}{estado_text}",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=10, pady=5)
        
        tk.Label(info_frame,
                text=f"Tipo: {alerta['tipo']}",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 11)).pack(anchor="w", padx=10, pady=5)
        
        # Área de nota
        tk.Label(dialog,
                text="Nota:",
                bg=COLORES["fondo"],
                fg=COLORES["texto"],
                font=("Segoe UI", 11, "bold")).pack(pady=(20, 5))
        
        texto_nota = tk.Text(dialog,
                            height=8,
                            width=50,
                            bg="#2d3047",
                            fg=COLORES["texto"],
                            font=("Segoe UI", 10),
                            wrap="word")
        texto_nota.pack(padx=20, pady=5)
        
        # Si ya existe una nota, mostrarla - CORREGIDO: usar "1.0" con comillas
        if "nota_pendiente" in alerta and alerta["nota_pendiente"]:
            texto_nota.insert("1.0", alerta["nota_pendiente"])
        
        # Frame para botones (SIEMPRE VISIBLE)
        btn_frame = tk.Frame(dialog, bg=COLORES["fondo"])
        btn_frame.pack(pady=20)
        
        def guardar_nota():
            nota = texto_nota.get("1.0", tk.END).strip()
            if nota:
                alerta["nota_pendiente"] = nota
                # No cambiar el estado, solo agregar nota
                
                # Guardar en BD
                guardar_falla(alerta, self.db_config)
                guardar_fallas_activas(self.fallas_activas, self.db_config)
                
                self.actualizar_tabla()
                self.update_stats()
                
                if self.ventana_proyeccion and self.frame_tabla_proyeccion:
                    self.actualizar_tabla_proyeccion()
                
                dialog.destroy()
                messagebox.showinfo("✅ Nota Guardada", 
                                "Nota agregada correctamente.")
            else:
                messagebox.showwarning("Aviso", 
                                    "La nota no puede estar vacía.", 
                                    parent=dialog)
        
        tk.Button(btn_frame,
                text="💾 Guardar Nota",
                bg=COLORES["success"],
                fg=COLORES["texto"],
                font=("Segoe UI", 11, "bold"),
                relief="flat",
                padx=20,
                pady=8,
                cursor="hand2",
                command=guardar_nota).pack(side="left", padx=5)
        
        tk.Button(btn_frame,
                text="❌ Cancelar",
                bg=COLORES["danger"],
                fg=COLORES["texto"],
                font=("Segoe UI", 11),
                relief="flat",
                padx=20,
                pady=8,
                cursor="hand2",
                command=dialog.destroy).pack(side="left", padx=5)
    
   #===============================================================

    def marcar_en_proceso(self, alerta):
        """Marca una falla como en proceso - CORREGIDO: verificar estado"""
        if alerta.get("estado") != "activa":
            messagebox.showinfo("Info", f"Esta falla está en estado '{alerta.get('estado')}' y no puede marcarse como en proceso.")
            return
            
        alerta["proceso"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        alerta["estado"] = "en_proceso"
        guardar_falla(alerta, self.db_config)
        guardar_fallas_activas(self.fallas_activas, self.db_config)
        self.actualizar_tabla()
        self.update_stats()
        
        if self.ventana_proyeccion and self.frame_tabla_proyeccion:
            self.actualizar_tabla_proyeccion()
        
    def finalizar_falla_manual(self, alerta):
        respuesta = messagebox.askyesno("Confirmar", f"¿Finalizar falla de máquina {alerta['maquina']}?")
        if respuesta:
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if "proceso" not in alerta or not alerta["proceso"]:
                alerta["proceso"] = ahora
            alerta["fin"] = ahora
            alerta["estado"] = "resuelta"

            # Guardar en BD (esto la moverá a historial y la eliminará de activas)
            if guardar_falla(alerta, self.db_config):
                # Eliminar de la lista en memoria
                if alerta in self.fallas_activas:
                    self.fallas_activas.remove(alerta)
                    if id(alerta) in self.numeros_falla_asignados:
                        del self.numeros_falla_asignados[id(alerta)]
                
                self.actualizar_tabla()
                self.update_stats()
                
                if self.ventana_proyeccion and self.frame_tabla_proyeccion:
                    self.actualizar_tabla_proyeccion()
                
                messagebox.showinfo("✅ Completado", "Falla finalizada y registrada.")
                    
    def debug_fallas_pendientes(self):
        """Función de depuración para verificar datos de pendientes"""
        print("\n=== DEBUG FALLAS PENDIENTES ===")
        print(f"Total fallas activas: {len(self.fallas_activas)}")
        
        pendientes = [a for a in self.fallas_activas if a.get("estado") == "pendiente"]
        print(f"Pendientes encontrados: {len(pendientes)}")
        
        for i, p in enumerate(pendientes):
            print(f"Pendiente {i+1}:")
            print(f"  Máquina: {p.get('maquina')}")
            print(f"  Tipo: {p.get('tipo')}")
            print(f"  Estado: {p.get('estado')}")
            print(f"  Nota: {p.get('nota_pendiente')}")
            print(f"  Fecha: {p.get('fecha_pendiente')}")
        
        print("===============================\n")
        
        messagebox.showinfo("Debug", 
                        f"Se encontraron {len(pendientes)} pendientes.\n"
                        "Revisa la consola para más detalles.")
        
    #================================================================

    def get_text_color_for_background(self, background_color):
        if self.is_light_color(background_color):
            return "#000000"
        else:
            return "#FFFFFF"

    def cargar_historial(self):
        """Carga el historial desde MySQL"""
        for widget in self.frame_historial_tabla.winfo_children():
            widget.destroy()
        
        if not self.mysql_disponible:
            messagebox.showerror("Error", "MySQL no está disponible")
            return
        
        try:
            conn = self._conectar_mysql()
            if not conn:
                messagebox.showerror("Error", "No se pudo conectar a MySQL")
                return
            
            cursor = conn.cursor(dictionary=True)
            
            query = "SELECT * FROM fallas WHERE 1=1"
            params = []
            
            if self.filtro_maquina.get():
                query += " AND maquina LIKE %s"
                params.append(f"%{self.filtro_maquina.get()}%")
            if self.filtro_tipo.get():
                query += " AND tipo = %s"
                params.append(self.filtro_tipo.get())
            if self.filtro_desde.get():
                query += " AND DATE(inicio) >= %s"
                params.append(self.filtro_desde.get_date().strftime("%Y-%m-%d"))
            if self.filtro_hasta.get():
                query += " AND DATE(fin) <= %s"
                params.append(self.filtro_hasta.get_date().strftime("%Y-%m-%d"))
            
            if self.filtro_estado.get():
                if self.filtro_estado.get() == "Fue Pendiente":
                    query += " AND fecha_pendiente IS NOT NULL"
                else:
                    estado_map = {
                        "Activa": "activa",
                        "En Proceso": "en_proceso",
                        "Pendiente": "pendiente",
                        "Resuelta": "resuelta"
                    }
                    estado_bd = estado_map.get(self.filtro_estado.get(), self.filtro_estado.get().lower())
                    query += " AND estado = %s"
                    params.append(estado_bd)
            
            query += " ORDER BY inicio DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            self.mostrar_resultados_historial(rows)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar historial:\n{str(e)}")


    def mostrar_resultados_historial(self, rows):
        tree_frame = ModernFrame(self.frame_historial_tabla)
        tree_frame.pack(fill="both", expand=True)

        columnas = ("ID", "Máquina", "Tipo", "Inicio", "Proceso", "Fin",
                    "# Falla", "T. Inicio-Proceso", "T. Proceso-Fin", "T. Total")

        tree = ttk.Treeview(tree_frame, columns=columnas, show="headings", style="Treeview")

        anchos = [60, 80, 100, 120, 120, 120, 70, 120, 120, 120]
        for col, ancho in zip(columnas, anchos):
            tree.heading(col, text=col)
            tree.column(col, width=ancho, anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for row in rows:
            if isinstance(row, dict):
                valores = (
                    row.get('id', ''),
                    row.get('maquina', ''),
                    row.get('tipo', ''),
                    row.get('inicio', ''),
                    row.get('proceso', ''),
                    row.get('fin', ''),
                    f"#{row.get('numero_falla', '')}",
                    row.get('t_inicio_proceso', ''),
                    row.get('t_proceso_fin', ''),
                    row.get('t_total', '')
                )
            else:
                row_list = list(row)
                while len(row_list) < 10:
                    row_list.append('')
                valores = tuple(row_list[:10])

            tree.insert("", "end", values=valores)

        self.ultimos_resultados = rows

        count_label = tk.Label(self.frame_historial_tabla,
                            text=f"Se encontraron {len(rows)} registros",
                            bg=COLORES["fondo"],
                            fg=COLORES["texto_secundario"],
                            font=("Segoe UI", 10))
        count_label.pack(side="bottom", pady=5)

    def exportar_excel_completo(self):
        if not self.puede_exportar_excel_con_graficos:
            self.exportar_excel_simple()
            return

        if self.excel_una_vez_dia:
            if not verificar_limite_excel_exports(self.licencia_config):
                messagebox.showwarning("Límite Diario",
                                    "Solo puedes exportar un Excel por día\n"
                                    "con tu licencia actual.")
                return

        if not hasattr(self, 'ultimos_resultados') or not self.ultimos_resultados:
            messagebox.showwarning("Aviso", "Primero realiza una búsqueda.")
            return

        # Seleccionar tipos a incluir (solo PRO)
        tipos_a_incluir = None
        if hasattr(self, 'puede_filtrar_tipos_graficas') and self.puede_filtrar_tipos_graficas:
            tipos_a_incluir = self.seleccionar_tipos_para_graficas()
            if not tipos_a_incluir:
                return  # Usuario canceló

        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                filetypes=[("Excel files", "*.xlsx")])
        if not file_path:
            return

        try:
            # Convertir a DataFrame
            if self.ultimos_resultados and isinstance(self.ultimos_resultados[0], dict):
                df = pd.DataFrame(self.ultimos_resultados)
            

            # Filtrar por tipos seleccionados
            if tipos_a_incluir and 'tipo' in df.columns:
                df = df[df['tipo'].isin(tipos_a_incluir)]
                if df.empty:
                    messagebox.showwarning("Sin datos", "No hay datos para los tipos seleccionados.")
                    return

                # Mapeo de columnas (ahora incluye nota_pendiente para todos)
                column_mapping = {
                    'id': 'ID',
                    'maquina': 'Máquina',
                    'tipo': 'Tipo',
                    'inicio': 'Inicio',
                    'proceso': 'Proceso',
                    'fin': 'Fin',
                    'numero_falla': '# Falla',
                    't_inicio_proceso': 'T. Inicio-Proceso',
                    't_proceso_fin': 'T. Proceso-Fin',
                    't_total': 'T. Total',
                    'estado': 'Estado',
                    'fecha_pendiente': 'Fecha Pendiente',
                    'nota_pendiente': 'Nota'  # ← SIEMPRE incluir, pero se mostrará según licencia
                }

                # Renombrar solo las columnas que existen
                for old_col, new_col in column_mapping.items():
                    if old_col in df.columns:
                        df.rename(columns={old_col: new_col}, inplace=True)

                # Columnas base que siempre deben estar
                columnas_exportar = ['ID', 'Máquina', 'Tipo', 'Inicio', 'Proceso', 'Fin', 
                                '# Falla', 'Estado', 'T. Inicio-Proceso', 'T. Proceso-Fin', 'T. Total']

                # Agregar Fecha Pendiente si existe
                if 'Fecha Pendiente' in df.columns:
                    columnas_exportar.append('Fecha Pendiente')

                # AGREGAR NOTA SOLO PARA MID Y PRO (no para BASIC)
                if self.licencia_config.get('license_type') in ['mid', 'pro', 'demo']:
                    if 'Nota' in df.columns:
                        columnas_exportar.append('Nota')
                        print("📝 Columna 'Nota' agregada al Excel (licencia MID/PRO)")
                    else:
                        # Si no existe la columna, crearla vacía
                        df['Nota'] = ""
                        columnas_exportar.append('Nota')
                        print("📝 Columna 'Nota' creada vacía para Excel")

                # Filtrar columnas que existen
                columnas_existentes = [col for col in columnas_exportar if col in df.columns]
                df = df[columnas_existentes]

                # Guardar Excel
                df.to_excel(file_path, index=False)
                
                # Agregar gráficas (solo para PRO y MID)
                if self.puede_ver_graficos:
                    wb = load_workbook(file_path)
                    self.agregar_graficas_a_excel(df, wb)
                    wb.save(file_path)

                messagebox.showinfo("Éxito", f"Datos exportados a {file_path}")

                if self.excel_una_vez_dia:
                    registrar_export_excel()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar: {str(e)}")
            import traceback
            traceback.print_exc()   
            
    def agregar_graficas_a_excel(self, df, wb):
        """Agrega TODAS las gráficas al archivo Excel (igual que en mostrar_todas_graficas)"""
        try:
            # Gráfica 1: Fallas por Tipo
            if 'Tipo' in df.columns:
                df_tipo = df["Tipo"].value_counts()
                if not df_tipo.empty:
                    fig1, ax1 = plt.subplots(figsize=(10, 6))
                    # Obtener colores para cada tipo
                    colores_barras = []
                    for tipo in df_tipo.index:
                        tipo_color_key = f"{tipo.lower().replace(' ', '_')}_color"
                        colores_barras.append(COLORES.get(tipo_color_key, "#FF5252"))
                    
                    df_tipo.plot(kind="bar", ax=ax1, title="Fallas por Tipo", color=colores_barras)
                    ax1.set_xlabel("Tipo de Falla")
                    ax1.set_ylabel("Cantidad")
                    ax1.tick_params(axis='x', rotation=45)
                    buf1 = io.BytesIO()
                    fig1.savefig(buf1, format='png', bbox_inches='tight', dpi=100)
                    plt.close(fig1)
                    buf1.seek(0)
                    ws1 = wb.create_sheet(title="Fallas por Tipo")
                    img1 = ExcelImage(buf1)
                    img1.anchor = 'A1'
                    ws1.add_image(img1)

            # Gráfica 2: Fallas por Máquina
            if 'Máquina' in df.columns:
                df_maq = df["Máquina"].value_counts()
                if not df_maq.empty:
                    fig2, ax2 = plt.subplots(figsize=(12, 6))
                    df_maq.plot(kind="bar", ax=ax2, title="Fallas por Máquina")
                    ax2.set_xlabel("Máquina")
                    ax2.set_ylabel("Cantidad")
                    ax2.tick_params(axis='x', rotation=45)
                    buf2 = io.BytesIO()
                    fig2.savefig(buf2, format='png', bbox_inches='tight', dpi=100)
                    plt.close(fig2)
                    buf2.seek(0)
                    ws2 = wb.create_sheet(title="Fallas por Máquina")
                    img2 = ExcelImage(buf2)
                    img2.anchor = 'A1'
                    ws2.add_image(img2)

            # Gráfica 3: Fallas por Tipo en cada Máquina (stacked)
            if 'Máquina' in df.columns and 'Tipo' in df.columns:
                try:
                    pivot = pd.pivot_table(df, index='Máquina', columns='Tipo',
                                        aggfunc='size', fill_value=0)
                    if not pivot.empty:
                        fig3, ax3 = plt.subplots(figsize=(14, 8))
                        # ¡CORREGIDO! Usar get_color_for_tipo para cada tipo
                        colores_para_grafica = []
                        for col in pivot.columns:
                            # Necesitamos acceder a self, pero estamos en una función fuera de la clase
                            # Usamos el diccionario global COLORES directamente
                            tipo_color_key = f"{col.lower().replace(' ', '_')}_color"
                            color = COLORES.get(tipo_color_key, "#FF5252")  # Rojo por defecto
                            colores_para_grafica.append(color)
                        
                        pivot.plot(kind="bar", stacked=True, ax=ax3, color=colores_para_grafica)
                        ax3.set_title("Fallas por Tipo en cada Máquina")
                        ax3.set_xlabel("Máquina")
                        ax3.set_ylabel("Cantidad de Fallas")
                        ax3.tick_params(axis='x', rotation=45)
                        ax3.legend(title="Tipo", bbox_to_anchor=(1.05, 1), loc='upper left')
                        buf3 = io.BytesIO()
                        fig3.savefig(buf3, format='png', bbox_inches='tight', dpi=100)
                        plt.close(fig3)
                        buf3.seek(0)
                        ws3 = wb.create_sheet(title="Fallas por Máq y Tipo")
                        img3 = ExcelImage(buf3)
                        img3.anchor = 'A1'
                        ws3.add_image(img3)
                except Exception as e:
                    print(f"Error en gráfica 3: {e}")

            # Gráfica 4: Tiempo Total Promedio por Tipo
            if 'T. Total' in df.columns and 'Tipo' in df.columns:
                try:
                    df['T. Total'] = df['T. Total'].astype(str)
                    try:
                        df['T. Total'] = pd.to_timedelta(df['T. Total'])
                    except:
                        df['T. Total'] = pd.to_timedelta(df['T. Total'].str.extract(r'(\d+:\d+:\d+)')[0])

                    df_total = df.groupby("Tipo")["T. Total"].mean().dropna()
                    if not df_total.empty:
                        df_total_horas = df_total.dt.total_seconds() / 3600
                        fig4, ax4 = plt.subplots(figsize=(10, 6))
                        df_total_horas.plot(kind="bar", ax=ax4, 
                                        title="Promedio del Tiempo Total por Tipo (horas)")
                        ax4.set_xlabel("Tipo")
                        ax4.set_ylabel("Horas Promedio")
                        ax4.tick_params(axis='x', rotation=45)
                        buf4 = io.BytesIO()
                        fig4.savefig(buf4, format='png', bbox_inches='tight', dpi=100)
                        plt.close(fig4)
                        buf4.seek(0)
                        ws4 = wb.create_sheet(title="Tiempo Total x Tipo")
                        img4 = ExcelImage(buf4)
                        img4.anchor = 'A1'
                        ws4.add_image(img4)
                except Exception as e:
                    print(f"Error en gráfica 4: {e}")

            # Gráfica 5: Promedio Inicio a Proceso
            if 'T. Inicio-Proceso' in df.columns and 'Tipo' in df.columns:
                try:
                    df['T. Inicio-Proceso'] = df['T. Inicio-Proceso'].astype(str)
                    try:
                        df['T. Inicio-Proceso'] = pd.to_timedelta(df['T. Inicio-Proceso'])
                    except:
                        df['T. Inicio-Proceso'] = pd.to_timedelta(df['T. Inicio-Proceso'].str.extract(r'(\d+:\d+:\d+)')[0])

                    df_ini_proc = df.groupby("Tipo")["T. Inicio-Proceso"].mean().dropna()
                    if not df_ini_proc.empty:
                        df_ini_proc_min = df_ini_proc.dt.total_seconds() / 60
                        fig5, ax5 = plt.subplots(figsize=(10, 6))
                        df_ini_proc_min.plot(kind="bar", ax=ax5,
                                        title="Promedio Inicio a Proceso (minutos)")
                        ax5.set_xlabel("Tipo")
                        ax5.set_ylabel("Minutos Promedio")
                        ax5.tick_params(axis='x', rotation=45)
                        buf5 = io.BytesIO()
                        fig5.savefig(buf5, format='png', bbox_inches='tight', dpi=100)
                        plt.close(fig5)
                        buf5.seek(0)
                        ws5 = wb.create_sheet(title="Inicio-Proceso")
                        img5 = ExcelImage(buf5)
                        img5.anchor = 'A1'
                        ws5.add_image(img5)
                except Exception as e:
                    print(f"Error en gráfica 5: {e}")

            # Gráfica 6: Promedio Proceso a Fin
            if 'T. Proceso-Fin' in df.columns and 'Tipo' in df.columns:
                try:
                    df['T. Proceso-Fin'] = df['T. Proceso-Fin'].astype(str)
                    try:
                        df['T. Proceso-Fin'] = pd.to_timedelta(df['T. Proceso-Fin'])
                    except:
                        df['T. Proceso-Fin'] = pd.to_timedelta(df['T. Proceso-Fin'].str.extract(r'(\d+:\d+:\d+)')[0])

                    df_proc_fin = df.groupby("Tipo")["T. Proceso-Fin"].mean().dropna()
                    if not df_proc_fin.empty:
                        df_proc_fin_min = df_proc_fin.dt.total_seconds() / 60
                        fig6, ax6 = plt.subplots(figsize=(10, 6))
                        df_proc_fin_min.plot(kind="bar", ax=ax6,
                                        title="Promedio Proceso a Fin (minutos)")
                        ax6.set_xlabel("Tipo")
                        ax6.set_ylabel("Minutos Promedio")
                        ax6.tick_params(axis='x', rotation=45)
                        buf6 = io.BytesIO()
                        fig6.savefig(buf6, format='png', bbox_inches='tight', dpi=100)
                        plt.close(fig6)
                        buf6.seek(0)
                        ws6 = wb.create_sheet(title="Proceso-Fin")
                        img6 = ExcelImage(buf6)
                        img6.anchor = 'A1'
                        ws6.add_image(img6)
                except Exception as e:
                    print(f"Error en gráfica 6: {e}")

            # Gráfica 7: Fallas por Estado (adicional)
            if 'Estado' in df.columns:
                df_estado = df["Estado"].value_counts()
                if not df_estado.empty:
                    fig7, ax7 = plt.subplots(figsize=(10, 6))
                    df_estado.plot(kind="bar", ax=ax7, title="Fallas por Estado")
                    ax7.set_xlabel("Estado")
                    ax7.set_ylabel("Cantidad")
                    ax7.tick_params(axis='x', rotation=45)
                    buf7 = io.BytesIO()
                    fig7.savefig(buf7, format='png', bbox_inches='tight', dpi=100)
                    plt.close(fig7)
                    buf7.seek(0)
                    ws7 = wb.create_sheet(title="Fallas por Estado")
                    img7 = ExcelImage(buf7)
                    img7.anchor = 'A1'
                    ws7.add_image(img7)

        except Exception as e:
            print(f"Error agregando gráficas: {e}")
            import traceback
            traceback.print_exc()

    def exportar_excel_simple(self):
        if not hasattr(self, 'ultimos_resultados') or not self.ultimos_resultados:
            messagebox.showwarning("Aviso", "Primero realiza una búsqueda.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                            filetypes=[("Excel files", "*.xlsx")])
        if not file_path:
            return

        try:
            if self.ultimos_resultados and isinstance(self.ultimos_resultados[0], dict):
                df = pd.DataFrame(self.ultimos_resultados)

                columnas_interes = ['id', 'maquina', 'tipo', 'inicio', 'proceso',
                                'fin', 't_inicio_proceso', 't_proceso_fin', 't_total', 'numero_falla']

                columnas_existentes = [col for col in columnas_interes if col in df.columns]
                df = df[columnas_existentes]

                nombre_map = {
                    'id': 'ID',
                    'maquina': 'Máquina',
                    'tipo': 'Tipo',
                    'inicio': 'Inicio',
                    'proceso': 'Proceso',
                    'fin': 'Fin',
                    't_inicio_proceso': 'T. Inicio-Proceso',
                    't_proceso_fin': 'T. Proceso-Fin',
                    't_total': 'T. Total',
                    'numero_falla': '# Falla'
                }
                df.rename(columns={k: v for k, v in nombre_map.items() if k in df.columns}, inplace=True)

            else:
                df = pd.DataFrame(self.ultimos_resultados,
                                columns=["ID", "Máquina", "Tipo", "Inicio", "Proceso",
                                        "Fin", "t_inicio_proceso", "t_proceso_fin",
                                        "t_total", "numero_falla", "created_at"])

                df = df[["ID", "Máquina", "Tipo", "Inicio", "Proceso", "Fin",
                        "numero_falla", "t_inicio_proceso", "t_proceso_fin", "t_total"]]

                df.rename(columns={
                    't_inicio_proceso': 'T. Inicio-Proceso',
                    't_proceso_fin': 'T. Proceso-Fin',
                    't_total': 'T. Total',
                    'numero_falla': '# Falla'
                }, inplace=True)

            df.to_excel(file_path, index=False)
            messagebox.showinfo("Éxito", f"Datos exportados a {file_path}")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar: {str(e)}")
            import traceback
            traceback.print_exc()
            
    def seleccionar_tipos_para_graficas(self):
        """Muestra un diálogo para seleccionar qué tipos de falla incluir en las gráficas"""
        if not hasattr(self, 'puede_filtrar_tipos_graficas') or not self.puede_filtrar_tipos_graficas:
            # Si no puede filtrar, devolver todos los tipos
            return self.tipos_falla

        dialog = tk.Toplevel(self.root)
        dialog.title("Seleccionar Tipos de Falla")
        dialog.geometry("400x500")
        dialog.configure(bg=COLORES["fondo"])
        dialog.transient(self.root)
        dialog.grab_set()

        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (400 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (500 // 2)
        dialog.geometry(f"+{x}+{y}")

        tk.Label(dialog, text="📊 Seleccionar Tipos de Falla", 
                bg=COLORES["fondo"], fg=COLORES["texto"], 
                font=("Segoe UI", 16, "bold")).pack(pady=20)

        # Frame con scroll para los checkboxes
        canvas_frame = tk.Frame(dialog, bg=COLORES["fondo"])
        canvas_frame.pack(fill="both", expand=True, padx=20, pady=10)

        canvas = tk.Canvas(canvas_frame, bg=COLORES["fondo"], highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORES["fondo"])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Variables para los checkboxes
        self.tipos_seleccionados_vars = {}
        
        tk.Label(scrollable_frame, text="Selecciona los tipos a incluir:", 
                bg=COLORES["fondo"], fg=COLORES["texto"], 
                font=("Segoe UI", 11)).pack(anchor="w", pady=(0, 10))

        for tipo in self.tipos_falla:
            var = tk.BooleanVar(value=True)  # Por defecto todos seleccionados
            self.tipos_seleccionados_vars[tipo] = var
            cb = tk.Checkbutton(scrollable_frame, text=tipo, variable=var,
                            bg=COLORES["fondo"], fg=COLORES["texto"],
                            selectcolor=COLORES["accento"],
                            font=("Segoe UI", 10))
            cb.pack(anchor="w", pady=2)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Botones
        btn_frame = tk.Frame(dialog, bg=COLORES["fondo"])
        btn_frame.pack(fill="x", padx=20, pady=20)

        resultado = []

        def aceptar():
            nonlocal resultado
            resultado = [tipo for tipo, var in self.tipos_seleccionados_vars.items() if var.get()]
            if not resultado:
                messagebox.showwarning("Selección vacía", "Debes seleccionar al menos un tipo.", parent=dialog)
                return
            dialog.destroy()

        def seleccionar_todos():
            for var in self.tipos_seleccionados_vars.values():
                var.set(True)

        def seleccionar_nadie():
            for var in self.tipos_seleccionados_vars.values():
                var.set(False)

        tk.Button(btn_frame, text="✅ Aceptar", command=aceptar,
                bg=COLORES["success"], fg=COLORES["texto"],
                font=("Segoe UI", 10, "bold"), relief="flat",
                padx=15, pady=5, cursor="hand2").pack(side="right", padx=5)

        tk.Button(btn_frame, text="❌ Cancelar", command=dialog.destroy,
                bg=COLORES["danger"], fg=COLORES["texto"],
                font=("Segoe UI", 10), relief="flat",
                padx=15, pady=5, cursor="hand2").pack(side="right", padx=5)

        tk.Button(btn_frame, text="✓ Todos", command=seleccionar_todos,
                bg=COLORES["card"], fg=COLORES["texto"],
                font=("Segoe UI", 9), relief="flat",
                padx=10, pady=3, cursor="hand2").pack(side="left", padx=5)

        tk.Button(btn_frame, text="✗ Ninguno", command=seleccionar_nadie,
                bg=COLORES["card"], fg=COLORES["texto"],
                font=("Segoe UI", 9), relief="flat",
                padx=10, pady=3, cursor="hand2").pack(side="left", padx=5)

        self.root.wait_window(dialog)
        return resultado if resultado else self.tipos_falla

    def mostrar_todas_graficas(self):
        if not self.puede_ver_graficos:
            messagebox.showinfo("Acceso Restringido",
                            "Las gráficas no están disponibles\n"
                            "con tu licencia actual.\n\n"
                            "Actualiza a una licencia MID o PRO para acceder.")
            return

        if not hasattr(self, 'ultimos_resultados') or not self.ultimos_resultados:
            messagebox.showwarning("Aviso", "Primero realiza una búsqueda.")
            return

        # Seleccionar tipos a incluir (solo PRO)
        tipos_a_incluir = None
        if hasattr(self, 'puede_filtrar_tipos_graficas') and self.puede_filtrar_tipos_graficas:
            tipos_a_incluir = self.seleccionar_tipos_para_graficas()
            if not tipos_a_incluir:
                return  # Usuario canceló
        else:
            # MID: todos los tipos
            tipos_a_incluir = self.tipos_falla

        try:
            # Convertir a DataFrame
            if self.ultimos_resultados and isinstance(self.ultimos_resultados[0], dict):
                df = pd.DataFrame(self.ultimos_resultados)
                print("📊 Columnas en MySQL:", df.columns.tolist())
            

            # Filtrar por tipos seleccionados
            if tipos_a_incluir and 'tipo' in df.columns:
                df = df[df['tipo'].isin(tipos_a_incluir)]
                if df.empty:
                    messagebox.showwarning("Sin datos", "No hay datos para los tipos seleccionados.")
                    return

            # Renombrar columnas para las gráficas
            column_mapping = {
                'tipo': 'Tipo',
                'maquina': 'Máquina',
                't_inicio_proceso': 'T. Inicio-Proceso',
                't_proceso_fin': 'T. Proceso-Fin',
                't_total': 'T. Total'
            }
            
            # Solo renombrar las columnas que existen
            for old_col, new_col in column_mapping.items():
                if old_col in df.columns:
                    df.rename(columns={old_col: new_col}, inplace=True)

            print("📊 Columnas después de procesar:", df.columns.tolist())

            plt.style.use('seaborn-v0_8-darkgrid')
            
            fig, axes = plt.subplots(2, 3, figsize=(18, 12))
            fig.suptitle("Análisis Completo de Fallas - Sistema Andon", fontsize=16, fontweight='bold')

            if not df.empty:
                # ===== GRÁFICA 1: Fallas por Tipo =====
                if 'Tipo' in df.columns:
                    tipo_counts = df['Tipo'].value_counts()
                    if not tipo_counts.empty:
                        # Obtener colores para cada tipo
                        colores_tipos = []
                        for tipo in tipo_counts.index:
                            color_key = f"{tipo.lower().replace(' ', '_')}_color"
                            color = COLORES.get(color_key, "#FF5252")
                            colores_tipos.append(color)
                        
                        tipo_counts.plot(kind="bar", ax=axes[0, 0],
                                    title="Fallas por Tipo de Error",
                                    color=colores_tipos)
                        axes[0, 0].set_xlabel("Tipo de Error")
                        axes[0, 0].set_ylabel("Cantidad")
                        axes[0, 0].tick_params(axis='x', rotation=45)
                    else:
                        axes[0, 0].text(0.5, 0.5, "Sin datos para esta gráfica",
                                    ha='center', va='center', transform=axes[0, 0].transAxes)
                else:
                    axes[0, 0].text(0.5, 0.5, "Columna 'Tipo' no encontrada",
                                ha='center', va='center', transform=axes[0, 0].transAxes)

                # ===== GRÁFICA 2: Fallas por Máquina =====
                if 'Máquina' in df.columns:
                    maquina_counts = df['Máquina'].value_counts()
                    if not maquina_counts.empty:
                        maquina_counts.plot(kind="bar", ax=axes[0, 1],
                                        title="Fallas por Máquina",
                                        color=COLORES["accento"])
                        axes[0, 1].set_xlabel("Máquina")
                        axes[0, 1].set_ylabel("Cantidad")
                        axes[0, 1].tick_params(axis='x', rotation=45)
                    else:
                        axes[0, 1].text(0.5, 0.5, "Sin datos para esta gráfica",
                                    ha='center', va='center', transform=axes[0, 1].transAxes)
                else:
                    axes[0, 1].text(0.5, 0.5, "Columna 'Máquina' no encontrada",
                                ha='center', va='center', transform=axes[0, 1].transAxes)

                # ===== GRÁFICA 3: Fallas por Tipo en cada Máquina =====
                try:
                    if 'Máquina' in df.columns and 'Tipo' in df.columns:
                        pivot = pd.pivot_table(df, index='Máquina', columns='Tipo',
                                            aggfunc='size', fill_value=0)
                        if not pivot.empty:
                            # Obtener colores para cada tipo
                            colores_apilados = []
                            for col in pivot.columns:
                                color_key = f"{col.lower().replace(' ', '_')}_color"
                                color = COLORES.get(color_key, "#FF5252")
                                colores_apilados.append(color)
                            
                            pivot.plot(kind="bar", stacked=True, ax=axes[0, 2],
                                    title="Fallas por Tipo en cada Máquina",
                                    color=colores_apilados)
                            axes[0, 2].set_xlabel("Máquina")
                            axes[0, 2].set_ylabel("Cantidad de Fallas")
                            axes[0, 2].tick_params(axis='x', rotation=45)
                            axes[0, 2].legend(title="Tipo", bbox_to_anchor=(1.05, 1), loc='upper left')
                        else:
                            axes[0, 2].text(0.5, 0.5, "Datos insuficientes\npara esta gráfica",
                                        ha='center', va='center', transform=axes[0, 2].transAxes)
                    else:
                        axes[0, 2].text(0.5, 0.5, "Columnas necesarias no encontradas",
                                    ha='center', va='center', transform=axes[0, 2].transAxes)
                except Exception as e:
                    print(f"Error en gráfica 3: {e}")
                    axes[0, 2].text(0.5, 0.5, f"Error: {str(e)[:50]}",
                                ha='center', va='center', transform=axes[0, 2].transAxes)

                # ===== GRÁFICA 4: Tiempo Total Promedio por Tipo =====
                try:
                    if 'T. Total' in df.columns:
                        # Convertir a timedelta
                        df['T. Total'] = df['T. Total'].astype(str)
                        try:
                            df['T. Total'] = pd.to_timedelta(df['T. Total'])
                        except:
                            df['T. Total'] = pd.to_timedelta(df['T. Total'].str.extract(r'(\d+:\d+:\d+)')[0])

                        if 'Tipo' in df.columns and not df['T. Total'].isna().all():
                            df_total = df.groupby("Tipo")["T. Total"].mean().dropna()
                            if not df_total.empty:
                                df_total_horas = df_total.dt.total_seconds() / 3600
                                # Obtener colores para cada tipo
                                colores_tiempo = []
                                for tipo in df_total_horas.index:
                                    color_key = f"{tipo.lower().replace(' ', '_')}_color"
                                    color = COLORES.get(color_key, "#FF5252")
                                    colores_tiempo.append(color)
                                
                                df_total_horas.plot(kind="bar", ax=axes[1, 0],
                                                title="Promedio del Tiempo Total por Tipo (horas)",
                                                color=colores_tiempo)
                                axes[1, 0].set_xlabel("Tipo")
                                axes[1, 0].set_ylabel("Horas Promedio")
                                axes[1, 0].tick_params(axis='x', rotation=45)
                            else:
                                axes[1, 0].text(0.5, 0.5, "Datos insuficientes\npara cálculo de tiempos",
                                            ha='center', va='center', transform=axes[1, 0].transAxes)
                        else:
                            axes[1, 0].text(0.5, 0.5, "Datos insuficientes\npara cálculo de tiempos",
                                        ha='center', va='center', transform=axes[1, 0].transAxes)
                    else:
                        axes[1, 0].text(0.5, 0.5, "Columna 'T. Total' no encontrada",
                                    ha='center', va='center', transform=axes[1, 0].transAxes)
                except Exception as e:
                    print(f"Error en gráfica 4: {e}")
                    axes[1, 0].text(0.5, 0.5, f"Error en tiempos totales",
                                ha='center', va='center', transform=axes[1, 0].transAxes)

                # ===== GRÁFICA 5: Promedio Inicio a Proceso =====
                try:
                    if 'T. Inicio-Proceso' in df.columns:
                        df['T. Inicio-Proceso'] = df['T. Inicio-Proceso'].astype(str)
                        try:
                            df['T. Inicio-Proceso'] = pd.to_timedelta(df['T. Inicio-Proceso'])
                        except:
                            df['T. Inicio-Proceso'] = pd.to_timedelta(df['T. Inicio-Proceso'].str.extract(r'(\d+:\d+:\d+)')[0])

                        if 'Tipo' in df.columns and not df['T. Inicio-Proceso'].isna().all():
                            df_ini_proc = df.groupby("Tipo")["T. Inicio-Proceso"].mean().dropna()
                            if not df_ini_proc.empty:
                                df_ini_proc_min = df_ini_proc.dt.total_seconds() / 60
                                # Obtener colores para cada tipo
                                colores_ini_proc = []
                                for tipo in df_ini_proc_min.index:
                                    color_key = f"{tipo.lower().replace(' ', '_')}_color"
                                    color = COLORES.get(color_key, "#FF5252")
                                    colores_ini_proc.append(color)
                                
                                df_ini_proc_min.plot(kind="bar", ax=axes[1, 1],
                                                title="Promedio Inicio a Proceso (minutos)",
                                                color=colores_ini_proc)
                                axes[1, 1].set_xlabel("Tipo")
                                axes[1, 1].set_ylabel("Minutos Promedio")
                                axes[1, 1].tick_params(axis='x', rotation=45)
                            else:
                                axes[1, 1].text(0.5, 0.5, "Datos insuficientes\npara cálculo de tiempos",
                                            ha='center', va='center', transform=axes[1, 1].transAxes)
                        else:
                            axes[1, 1].text(0.5, 0.5, "Datos insuficientes\npara cálculo de tiempos",
                                        ha='center', va='center', transform=axes[1, 1].transAxes)
                    else:
                        axes[1, 1].text(0.5, 0.5, "Columna 'T. Inicio-Proceso' no encontrada",
                                    ha='center', va='center', transform=axes[1, 1].transAxes)
                except Exception as e:
                    print(f"Error en gráfica 5: {e}")
                    axes[1, 1].text(0.5, 0.5, f"Error en tiempos inicio-proceso",
                                ha='center', va='center', transform=axes[1, 1].transAxes)

                # ===== GRÁFICA 6: Promedio Proceso a Fin =====
                try:
                    if 'T. Proceso-Fin' in df.columns:
                        df['T. Proceso-Fin'] = df['T. Proceso-Fin'].astype(str)
                        try:
                            df['T. Proceso-Fin'] = pd.to_timedelta(df['T. Proceso-Fin'])
                        except:
                            df['T. Proceso-Fin'] = pd.to_timedelta(df['T. Proceso-Fin'].str.extract(r'(\d+:\d+:\d+)')[0])

                        if 'Tipo' in df.columns and not df['T. Proceso-Fin'].isna().all():
                            df_proc_fin = df.groupby("Tipo")["T. Proceso-Fin"].mean().dropna()
                            if not df_proc_fin.empty:
                                df_proc_fin_min = df_proc_fin.dt.total_seconds() / 60
                                # Obtener colores para cada tipo
                                colores_proc_fin = []
                                for tipo in df_proc_fin_min.index:
                                    color_key = f"{tipo.lower().replace(' ', '_')}_color"
                                    color = COLORES.get(color_key, "#FF5252")
                                    colores_proc_fin.append(color)
                                
                                df_proc_fin_min.plot(kind="bar", ax=axes[1, 2],
                                                title="Promedio Proceso a Fin (minutos)",
                                                color=colores_proc_fin)
                                axes[1, 2].set_xlabel("Tipo")
                                axes[1, 2].set_ylabel("Minutos Promedio")
                                axes[1, 2].tick_params(axis='x', rotation=45)
                            else:
                                axes[1, 2].text(0.5, 0.5, "Datos insuficientes\npara cálculo de tiempos",
                                            ha='center', va='center', transform=axes[1, 2].transAxes)
                        else:
                            axes[1, 2].text(0.5, 0.5, "Datos insuficientes\npara cálculo de tiempos",
                                        ha='center', va='center', transform=axes[1, 2].transAxes)
                    else:
                        axes[1, 2].text(0.5, 0.5, "Columna 'T. Proceso-Fin' no encontrada",
                                    ha='center', va='center', transform=axes[1, 2].transAxes)
                except Exception as e:
                    print(f"Error en gráfica 6: {e}")
                    axes[1, 2].text(0.5, 0.5, f"Error en tiempos proceso-fin",
                                ha='center', va='center', transform=axes[1, 2].transAxes)
            else:
                for ax in axes.flat:
                    ax.text(0.5, 0.5, "No hay datos para mostrar",
                        ha='center', va='center', transform=ax.transAxes)

            plt.tight_layout()
            plt.show()

        except Exception as e:
            messagebox.showerror("Error al mostrar gráficas", f"Error: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def toggle_proyeccion(self):
        if not self.puede_configurar_proyeccion and not self.ventana_proyeccion:
            self.abrir_proyeccion_simple()
            return

        if self.ventana_proyeccion and self.ventana_proyeccion.winfo_exists():
            self.ventana_proyeccion.destroy()
            self.ventana_proyeccion = None
            self.frame_tabla_proyeccion = None
            return
        
        if not self.puede_configurar_proyeccion:
            self.abrir_proyeccion_simple()
            return
        
        # Para MID/PRO: mostrar diálogo de configuración
        self.mostrar_dialogo_proyeccion()

    def abrir_proyeccion_simple(self):
        self.ventana_proyeccion = tk.Toplevel(self.root)
        self.ventana_proyeccion.title(f"{self.nombre_sistema} - Vista de Proyección")
        self.ventana_proyeccion.configure(bg="black")
        self.ventana_proyeccion.geometry("800x600")
        self.ventana_proyeccion.resizable(True, True)

        header = tk.Frame(self.ventana_proyeccion, bg="black")
        header.pack(fill="x", pady=10)

        tk.Label(header,
                text=f"📺 {self.nombre_sistema} - PROYECCIÓN",
                bg="black",
                fg="white",
                font=("Segoe UI", 20, "bold")).pack()

        tk.Label(header,
                text="Fallas Activas en Tiempo Real",
                bg="black",
                fg="#e94560",
                font=("Segoe UI", 14)).pack(pady=5)

        contador_frame = tk.Frame(header, bg="black")
        contador_frame.pack(pady=10)

        self.proj_counter = tk.Label(contador_frame,
                                    text=str(len(self.fallas_activas)),
                                    bg="black",
                                    fg="white",
                                    font=("Segoe UI", 36, "bold"))
        self.proj_counter.pack(side="left")

        tk.Label(contador_frame,
                text="fallas activas",
                bg="black",
                fg="white",
                font=("Segoe UI", 12)).pack(side="left", padx=5)

        self.frame_tabla_proyeccion = tk.Frame(self.ventana_proyeccion, bg="black")
        self.frame_tabla_proyeccion.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.actualizar_tabla_proyeccion()
        self.iniciar_actualizacion_proyeccion()

    def mostrar_dialogo_proyeccion(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Configurar Proyección")
        dialog.geometry("600x700")
        dialog.configure(bg=COLORES["fondo"])
        dialog.resizable(True, True)
        dialog.transient(self.root)
        dialog.grab_set()

        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (600 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (700 // 2)
        dialog.geometry(f"600x700+{x}+{y}")

        main_frame = tk.Frame(dialog, bg=COLORES["fondo"])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(main_frame,
                text="📺 Configurar Vista de Proyección",
                bg=COLORES["fondo"],
                fg=COLORES["texto"],
                font=("Segoe UI", 16, "bold")).pack(pady=(0, 20))

        canvas_frame = tk.Frame(main_frame, bg=COLORES["fondo"])
        canvas_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(canvas_frame, bg=COLORES["fondo"], highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORES["fondo"])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        colores_card = tk.Frame(scrollable_frame, bg=COLORES["card"], relief="flat", bd=1,
                            highlightbackground=COLORES["texto_secundario"])
        colores_card.pack(fill="x", pady=(0, 15))

        tk.Label(colores_card,
                text="🎨 Personalización de Colores",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15, pady=(15, 10))

        fondo_frame = tk.Frame(colores_card, bg=COLORES["card"])
        fondo_frame.pack(fill="x", padx=15, pady=5)

        tk.Label(fondo_frame,
                text="Color de Fondo:",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 10),
                width=20,
                anchor="w").pack(side="left")

        self.proy_fondo_color = tk.StringVar(value=self.config_proyeccion.get("color_fondo", "#000000"))
        fondo_preview = tk.Frame(fondo_frame, bg=self.proy_fondo_color.get(), width=50, height=25)
        fondo_preview.pack(side="left", padx=5)
        fondo_preview.pack_propagate(False)

        tk.Button(fondo_frame,
                text="Cambiar",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 8),
                relief="flat",
                padx=10,
                pady=2,
                cursor="hand2",
                command=lambda: self.cambiar_color_proyeccion("fondo", fondo_preview)).pack(side="left", padx=5)

        texto_frame = tk.Frame(colores_card, bg=COLORES["card"])
        texto_frame.pack(fill="x", padx=15, pady=5)

        tk.Label(texto_frame,
                text="Color de Texto:",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 10),
                width=20,
                anchor="w").pack(side="left")

        self.proy_texto_color = tk.StringVar(value=self.config_proyeccion.get("color_texto", "#FFFFFF"))
        texto_preview = tk.Frame(texto_frame, bg=self.proy_texto_color.get(), width=50, height=25)
        texto_preview.pack(side="left", padx=5)
        texto_preview.pack_propagate(False)

        tk.Button(texto_frame,
                text="Cambiar",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 8),
                relief="flat",
                padx=10,
                pady=2,
                cursor="hand2",
                command=lambda: self.cambiar_color_proyeccion("texto", texto_preview)).pack(side="left", padx=5)

        acento_frame = tk.Frame(colores_card, bg=COLORES["card"])
        acento_frame.pack(fill="x", padx=15, pady=5)

        tk.Label(acento_frame,
                text="Color de Acento:",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 10),
                width=20,
                anchor="w").pack(side="left")

        self.proy_acento_color = tk.StringVar(value=self.config_proyeccion.get("color_acento", "#e94560"))
        acento_preview = tk.Frame(acento_frame, bg=self.proy_acento_color.get(), width=50, height=25)
        acento_preview.pack(side="left", padx=5)
        acento_preview.pack_propagate(False)

        tk.Button(acento_frame,
                text="Cambiar",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 8),
                relief="flat",
                padx=10,
                pady=2,
                cursor="hand2",
                command=lambda: self.cambiar_color_proyeccion("acento", acento_preview)).pack(side="left", padx=5)

        exito_frame = tk.Frame(colores_card, bg=COLORES["card"])
        exito_frame.pack(fill="x", padx=15, pady=5)

        tk.Label(exito_frame,
                text="Color de Éxito:",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 10),
                width=20,
                anchor="w").pack(side="left")

        self.proy_exito_color = tk.StringVar(value=self.config_proyeccion.get("color_exito", "#4CAF50"))
        exito_preview = tk.Frame(exito_frame, bg=self.proy_exito_color.get(), width=50, height=25)
        exito_preview.pack(side="left", padx=5)
        exito_preview.pack_propagate(False)

        tk.Button(exito_frame,
                text="Cambiar",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 8),
                relief="flat",
                padx=10,
                pady=2,
                cursor="hand2",
                command=lambda: self.cambiar_color_proyeccion("exito", exito_preview)).pack(side="left", padx=5)

        visual_card = tk.Frame(scrollable_frame, bg=COLORES["card"], relief="flat", bd=1,
                            highlightbackground=COLORES["texto_secundario"])
        visual_card.pack(fill="x", pady=(0, 15))

        tk.Label(visual_card,
                text="👁️ Opciones de Visualización",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15, pady=(15, 10))

        self.mostrar_contador_var = tk.BooleanVar(value=self.config_proyeccion.get("mostrar_contador", True))
        tk.Checkbutton(visual_card,
                    text="Mostrar contador de fallas activas",
                    variable=self.mostrar_contador_var,
                    bg=COLORES["card"],
                    fg=COLORES["texto"],
                    selectcolor=COLORES["accento"],
                    font=("Segoe UI", 10)).pack(anchor="w", padx=15, pady=5)
        
        # NUEVA OPCIÓN: Mostrar/ocultar pendientes
        self.mostrar_pendientes_var = tk.BooleanVar(value=self.config_proyeccion.get("mostrar_pendientes", True))
        tk.Checkbutton(visual_card,
                    text="Mostrar fallas pendientes en la tabla",
                    variable=self.mostrar_pendientes_var,
                    bg=COLORES["card"],
                    fg=COLORES["texto"],
                    selectcolor=COLORES["accento"],
                    font=("Segoe UI", 10)).pack(anchor="w", padx=15, pady=5)

        contador_card = tk.Frame(scrollable_frame, bg=COLORES["card"], relief="flat", bd=1,
                                highlightbackground=COLORES["texto_secundario"])
        contador_card.pack(fill="x", pady=(0, 15))

        tk.Label(contador_card,
                text="🔢 Configuración del Contador de Fallas",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15, pady=(15, 10))

        periodo_frame = tk.Frame(contador_card, bg=COLORES["card"])
        periodo_frame.pack(fill="x", padx=15, pady=5)

        tk.Label(periodo_frame,
                text="Reiniciar contador cada:",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 10)).pack(anchor="w")

        self.periodo_reset_var = tk.StringVar(value=self.config_contador.get("periodo_reset", "diario"))
        periodos = [
            ("12 horas", "horas_12"),
            ("Diario", "diario"),
            ("Semanal", "semanal"),
            ("Mensual", "mensual"),
            ("Anual", "anual"),
            ("Nunca", "nunca")
        ]

        for texto, valor in periodos:
            rb_frame = tk.Frame(periodo_frame, bg=COLORES["card"])
            rb_frame.pack(fill="x", pady=2)
            tk.Radiobutton(rb_frame,
                        text=texto,
                        variable=self.periodo_reset_var,
                        value=valor,
                        bg=COLORES["card"],
                        fg=COLORES["texto"],
                        selectcolor=COLORES["accento"],
                        font=("Segoe UI", 9)).pack(anchor="w", padx=20)

        info_frame = tk.Frame(contador_card, bg=COLORES["card"])
        info_frame.pack(fill="x", padx=15, pady=10)

        ultimo_reset = datetime.strptime(self.config_contador["ultimo_reset"], "%Y-%m-%d %H:%M:%S")
        tk.Label(info_frame,
                text=f"Último reset: {ultimo_reset.strftime('%d/%m/%Y %H:%M')}",
                bg=COLORES["card"],
                fg=COLORES["texto_secundario"],
                font=("Segoe UI", 9)).pack(anchor="w")

        tk.Label(info_frame,
                text=f"Número actual: {self.config_contador['consecutivo_actual']}",
                bg=COLORES["card"],
                fg=COLORES["success"],
                font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=2)

        tk.Button(info_frame,
                text="🔄 Resetear Contador Ahora",
                bg=COLORES["warning"],
                fg=COLORES["negro"],
                font=("Segoe UI", 9),
                relief="flat",
                padx=10,
                pady=3,
                cursor="hand2",
                command=self.resetear_contador_manual).pack(anchor="w", pady=5)

        modo_card = tk.Frame(scrollable_frame, bg=COLORES["card"], relief="flat", bd=1,
                            highlightbackground=COLORES["texto_secundario"])
        modo_card.pack(fill="x", pady=(0, 15))

        tk.Label(modo_card,
                text="🖥️ Modo de Visualización",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15, pady=(15, 10))

        modo_frame = tk.Frame(modo_card, bg=COLORES["card"])
        modo_frame.pack(fill="x", padx=15, pady=5)

        self.modo_var = tk.StringVar(value="ventana" if not self.config_proyeccion["pantalla_completa"] else "completa")

        tk.Radiobutton(modo_frame,
                    text="🖥️ Ventana Movible",
                    variable=self.modo_var,
                    value="ventana",
                    bg=COLORES["card"],
                    fg=COLORES["texto"],
                    selectcolor=COLORES["accento"],
                    font=("Segoe UI", 10),
                    command=self.actualizar_opciones_modo).pack(anchor="w", pady=5)

        self.tamano_frame = tk.Frame(modo_card, bg=COLORES["card"])

        tk.Label(self.tamano_frame,
                text="Tamaño y Posición:",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(10, 10))

        dim_frame = tk.Frame(self.tamano_frame, bg=COLORES["card"])
        dim_frame.pack(fill="x", pady=5)

        tk.Label(dim_frame,
                text="Ancho:",
                bg=COLORES["card"],
                fg=COLORES["texto_secundario"],
                font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))

        self.ancho_var = tk.StringVar(value=str(self.config_proyeccion["ancho"]))
        ancho_entry = tk.Entry(dim_frame,
                            textvariable=self.ancho_var,
                            width=8,
                            bg="#2d3047",
                            fg=COLORES["texto"],
                            relief="flat",
                            font=("Segoe UI", 10))
        ancho_entry.pack(side="left", padx=(0, 20))

        tk.Label(dim_frame,
                text="Alto:",
                bg=COLORES["card"],
                fg=COLORES["texto_secundario"],
                font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))

        self.alto_var = tk.StringVar(value=str(self.config_proyeccion["alto"]))
        alto_entry = tk.Entry(dim_frame,
                            textvariable=self.alto_var,
                            width=8,
                            bg="#2d3047",
                            fg=COLORES["texto"],
                            relief="flat",
                            font=("Segoe UI", 10))
        alto_entry.pack(side="left")

        pos_frame = tk.Frame(self.tamano_frame, bg=COLORES["card"])
        pos_frame.pack(fill="x", pady=5)

        tk.Label(pos_frame,
                text="Posición X:",
                bg=COLORES["card"],
                fg=COLORES["texto_secundario"],
                font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))

        self.x_var = tk.StringVar(value=str(self.config_proyeccion["x"]))
        x_entry = tk.Entry(pos_frame,
                        textvariable=self.x_var,
                        width=8,
                        bg="#2d3047",
                        fg=COLORES["texto"],
                        relief="flat",
                        font=("Segoe UI", 10))
        x_entry.pack(side="left", padx=(0, 20))

        tk.Label(pos_frame,
                text="Posición Y:",
                bg=COLORES["card"],
                fg=COLORES["texto_secundario"],
                font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))

        self.y_var = tk.StringVar(value=str(self.config_proyeccion["y"]))
        y_entry = tk.Entry(pos_frame,
                        textvariable=self.y_var,
                        width=8,
                        bg="#2d3047",
                        fg=COLORES["texto"],
                        relief="flat",
                        font=("Segoe UI", 10))
        y_entry.pack(side="left")

        monitor_frame = tk.Frame(scrollable_frame, bg=COLORES["card"])
        monitor_frame.pack(fill="x", pady=(0, 15))

        tk.Label(monitor_frame,
                text="Seleccionar Monitor:",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15, pady=(15, 10))

        self.monitor_var = tk.IntVar(value=self.config_proyeccion.get("monitor", 0))
        self.monitor_list_frame = tk.Frame(monitor_frame, bg=COLORES["card"])
        self.monitor_list_frame.pack(fill="x", padx=15, pady=5)

        detect_btn = tk.Button(monitor_frame,
                            text="🔍 Detectar Pantallas Disponibles",
                            bg=COLORES["accento"],
                            fg=COLORES["texto"],
                            font=("Segoe UI", 10),
                            relief="flat",
                            padx=15,
                            pady=5,
                            cursor="hand2",
                            command=lambda: self.detectar_pantallas(self.monitor_list_frame))
        detect_btn.pack(pady=10)

        opciones_frame = tk.Frame(scrollable_frame, bg=COLORES["card"])
        opciones_frame.pack(fill="x", pady=(0, 20))

        self.recordar_var = tk.BooleanVar(value=self.config_proyeccion["recordar_posicion"])
        tk.Checkbutton(opciones_frame,
                    text="💾 Recordar posición y tamaño",
                    variable=self.recordar_var,
                    bg=COLORES["card"],
                    fg=COLORES["texto"],
                    selectcolor=COLORES["accento"],
                    font=("Segoe UI", 10)).pack(anchor="w", padx=15, pady=5)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        button_frame = tk.Frame(main_frame, bg=COLORES["fondo"])
        button_frame.pack(fill="x", pady=(20, 0))

        tk.Button(button_frame,
                text="🚫 Cancelar",
                bg=COLORES["danger"],
                fg=COLORES["texto"],
                font=("Segoe UI", 11),
                relief="flat",
                padx=20,
                pady=10,
                cursor="hand2",
                command=dialog.destroy).pack(side="left", padx=5)

        tk.Button(button_frame,
                text="✅ Abrir Proyección",
                bg=COLORES["success"],
                fg=COLORES["texto"],
                font=("Segoe UI", 11, "bold"),
                relief="flat",
                padx=20,
                pady=10,
                cursor="hand2",
                command=lambda: self.abrir_proyeccion_configurada(dialog)).pack(side="right", padx=5)

        self.actualizar_opciones_modo()
        self.detectar_pantallas(self.monitor_list_frame)

    def cambiar_color_proyeccion(self, tipo, preview_frame):
        if tipo == "fondo":
            titulo = "Color de Fondo"
            var = self.proy_fondo_color
        elif tipo == "texto":
            titulo = "Color de Texto"
            var = self.proy_texto_color
        elif tipo == "acento":
            titulo = "Color de Acento"
            var = self.proy_acento_color
        elif tipo == "exito":
            titulo = "Color de Éxito"
            var = self.proy_exito_color
        else:
            return

        color = colorchooser.askcolor(title=titulo, initialcolor=var.get())
        if color[1]:
            var.set(color[1])
            preview_frame.config(bg=color[1])

    def resetear_contador_manual(self):
        respuesta = messagebox.askyesno(
            "Confirmar Reset",
            "¿Estás seguro de resetear el contador de fallas?\n\n"
            "Esto reiniciará la numeración de las próximas fallas."
        )

        if respuesta:
            self.config_contador["consecutivo_actual"] = 0
            self.config_contador["ultimo_reset"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            guardar_config_contador(self.config_contador, self.db_config)

            messagebox.showinfo("✅ Reset Completado",
                              "El contador ha sido reseteado.\n"
                              "La próxima falla será la #1.")

    def actualizar_opciones_modo(self):
        if self.modo_var.get() == "ventana":
            self.tamano_frame.pack(fill="x", pady=(0, 20))
        else:
            self.tamano_frame.pack_forget()

    def detectar_pantallas(self, parent_frame=None):
        try:
            if parent_frame:
                for widget in parent_frame.winfo_children():
                    widget.destroy()
            pantallas = []
            try:
                from screeninfo import get_monitors
                monitores = get_monitors()
                for i, monitor in enumerate(monitores, 0):
                    pantallas.append({
                        "id": i,
                        "name": f"Monitor {i+1}",
                        "width": monitor.width,
                        "height": monitor.height,
                        "x": monitor.x,
                        "y": monitor.y,
                        "info": f"{monitor.width}x{monitor.height} (Posición: {monitor.x},{monitor.y})"
                    })
            except ImportError:
                import ctypes
                user32 = ctypes.windll.user32
                pantallas.append({
                    "id": 0,
                    "name": "Monitor 1",
                    "width": user32.GetSystemMetrics(0),
                    "height": user32.GetSystemMetrics(1),
                    "x": 0,
                    "y": 0,
                    "info": f"{user32.GetSystemMetrics(0)}x{user32.GetSystemMetrics(1)} (Posición: 0,0)"
                })
            if parent_frame:
                tk.Label(parent_frame,
                        text="Selecciona un monitor:",
                        bg=COLORES["card"],
                        fg=COLORES["texto_secundario"],
                        font=("Segoe UI", 9)).pack(anchor="w", pady=(5, 10))
                for pantalla in pantallas:
                    frame = tk.Frame(parent_frame, bg=COLORES["card"])
                    frame.pack(fill="x", pady=2)
                    rb = tk.Radiobutton(frame,
                                       text=f"{pantalla['name']}: {pantalla['info']}",
                                       variable=self.monitor_var,
                                       value=pantalla["id"],
                                       bg=COLORES["card"],
                                       fg=COLORES["texto"],
                                       selectcolor=COLORES["accento"],
                                       font=("Segoe UI", 9),
                                       anchor="w")
                    rb.pack(side="left", padx=10)
                    if pantalla["id"] == self.config_proyeccion.get("monitor", 0):
                        rb.select()
            self.monitores_detectados = pantallas
            return pantallas
        except Exception as e:
            if parent_frame:
                tk.Label(parent_frame,
                        text=f"Error detectando pantallas: {str(e)}",
                        bg=COLORES["card"],
                        fg=COLORES["danger"],
                        font=("Segoe UI", 9)).pack(pady=10)
            self.monitores_detectados = [{
                "id": 0,
                "name": "Monitor Principal",
                "width": 1920,
                "height": 1080,
                "x": 0,
                "y": 0,
                "info": "1920x1080 (Monitor principal)"
            }]
            return self.monitores_detectados

    def abrir_proyeccion_configurada(self, dialog):
        try:
            self.config_proyeccion["color_fondo"] = self.proy_fondo_color.get()
            self.config_proyeccion["color_texto"] = self.proy_texto_color.get()
            self.config_proyeccion["color_acento"] = self.proy_acento_color.get()
            self.config_proyeccion["color_exito"] = self.proy_exito_color.get()
            self.config_proyeccion["mostrar_contador"] = self.mostrar_contador_var.get()

            self.config_contador["periodo_reset"] = self.periodo_reset_var.get()
            guardar_config_contador(self.config_contador, self.db_config)  
            
            self.config_proyeccion["pantalla_completa"] = (self.modo_var.get() == "completa")
            self.config_proyeccion["recordar_posicion"] = self.recordar_var.get()
            self.config_proyeccion["monitor"] = self.monitor_var.get()
            
            self.config_proyeccion["mostrar_pendientes"] = self.mostrar_pendientes_var.get()


            if self.modo_var.get() == "ventana":
                try:
                    self.config_proyeccion["ancho"] = int(self.ancho_var.get())
                    self.config_proyeccion["alto"] = int(self.alto_var.get())
                    self.config_proyeccion["x"] = int(self.x_var.get())
                    self.config_proyeccion["y"] = int(self.y_var.get())
                except ValueError:
                    messagebox.showerror("Error", "Por favor ingresa valores numéricos válidos")
                    return

            guardar_config_proyeccion(self.config_proyeccion, self.db_config)  # ✅ ESTO SE QUEDA
            dialog.destroy()
            self.root.after(100, self.abrir_proyeccion)

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la proyección: {str(e)}")
        
    def abrir_proyeccion(self):
        self.ventana_proyeccion = tk.Toplevel(self.root)
        self.ventana_proyeccion.title(f"{self.nombre_sistema} - Vista de Proyección")

        fondo_color = self.config_proyeccion.get("color_fondo", "black")
        self.ventana_proyeccion.configure(bg=fondo_color)

        monitor_idx = self.config_proyeccion.get("monitor", 0)
        if hasattr(self, 'monitores_detectados') and len(self.monitores_detectados) > monitor_idx:
            monitor = self.monitores_detectados[monitor_idx]
        else:
            monitor = {"x": 0, "y": 0, "width": 1920, "height": 1080}

        if self.config_proyeccion["pantalla_completa"]:
            if monitor_idx > 0:
                self.ventana_proyeccion.geometry(f"{monitor['width']}x{monitor['height']}+{monitor['x']}+{monitor['y']}")
            self.ventana_proyeccion.attributes('-fullscreen', True)
            self.ventana_proyeccion.bind('<Escape>', lambda e: self.salir_pantalla_completa())
            self.ventana_proyeccion.update_idletasks()
            if monitor_idx > 0:
                self.ventana_proyeccion.geometry(f"+{monitor['x']}+{monitor['y']}")
                self.ventana_proyeccion.update()
        else:
            ancho = self.config_proyeccion["ancho"]
            alto = self.config_proyeccion["alto"]
            x = self.config_proyeccion["x"] + monitor["x"]
            y = self.config_proyeccion["y"] + monitor["y"]
            ancho = max(800, min(ancho, monitor["width"]))
            alto = max(600, min(alto, monitor["height"]))
            x = max(monitor["x"], min(x, monitor["x"] + monitor["width"] - ancho))
            y = max(monitor["y"], min(y, monitor["y"] + monitor["height"] - alto))
            self.ventana_proyeccion.geometry(f"{ancho}x{alto}+{x}+{y}")
            self.ventana_proyeccion.resizable(True, True)
            self.ventana_proyeccion.attributes('-topmost', True)

        self.ventana_proyeccion.protocol("WM_DELETE_WINDOW", self.cerrar_proyeccion)

        if not self.config_proyeccion["pantalla_completa"]:
            self.crear_menu_controles_proyeccion()

        header = tk.Frame(self.ventana_proyeccion, bg=fondo_color)
        header.pack(fill="x", pady=10)

        texto_color = self.config_proyeccion.get("color_texto", "white")
        acento_color = self.config_proyeccion.get("color_acento", "#e94560")
        exito_color = self.config_proyeccion.get("color_exito", "#4CAF50")

        tk.Label(header,
                text=f"📺 {self.nombre_sistema} - PROYECCIÓN",
                bg=fondo_color,
                fg=texto_color,
                font=("Segoe UI", 20, "bold")).pack()

        tk.Label(header,
                text="Fallas Activas en Tiempo Real",
                bg=fondo_color,
                fg="white",
                font=("Segoe UI", 14)).pack(pady=5)

        if self.config_proyeccion.get("mostrar_contador", True):
            contador_frame = tk.Frame(header, bg=fondo_color)
            contador_frame.pack(pady=10)

            self.proj_counter = tk.Label(contador_frame,
                                        text=str(len(self.fallas_activas)),
                                        bg=fondo_color,
                                        fg=texto_color,
                                        font=("Segoe UI", 36, "bold"))
            self.proj_counter.pack(side="left")

            tk.Label(contador_frame,
                    text="fallas activas",
                    bg=fondo_color,
                    fg=texto_color,
                    font=("Segoe UI", 12)).pack(side="left", padx=5)

        tiempo_frame = tk.Frame(header, bg=fondo_color)
        tiempo_frame.pack(pady=5)

        self.hora_actual = tk.Label(tiempo_frame,
                                text=datetime.now().strftime("%H:%M:%S"),
                                bg=fondo_color,
                                fg=exito_color,
                                font=("Segoe UI", 30, "bold"))
        self.hora_actual.pack(side="left", padx=5)

        tk.Label(tiempo_frame,
                text="|",
                bg=fondo_color,
                fg="white",
                font=("Segoe UI", 12)).pack(side="left", padx=5)

        self.fecha_actual = tk.Label(tiempo_frame,
                                    text=datetime.now().strftime("%d/%m/%Y"),
                                    bg=fondo_color,
                                    fg="white",
                                    font=("Segoe UI", 30))
        self.fecha_actual.pack(side="left", padx=5)

        self.frame_tabla_proyeccion = tk.Frame(self.ventana_proyeccion, bg=fondo_color)
        self.frame_tabla_proyeccion.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.actualizar_tabla_proyeccion()
        self.actualizar_hora_proyeccion()

        if self.config_proyeccion["pantalla_completa"]:
            self.crear_boton_flotante_pantalla_completa()

        self.iniciar_actualizacion_proyeccion()

    def iniciar_actualizacion_proyeccion(self):
        """Inicia la actualización periódica de la ventana de proyección"""
        # Cancelar timer anterior si existe
        if self.timer_proyeccion:
            try:
                self.root.after_cancel(self.timer_proyeccion)
            except:
                pass
            self.timer_proyeccion = None
        
        def actualizar_periodicamente():
            try:
                # Verificar que la ventana sigue existiendo
                if self.ventana_proyeccion and self.ventana_proyeccion.winfo_exists():
                    self.actualizar_tabla_proyeccion()
                    # Programar la siguiente actualización
                    self.timer_proyeccion = self.root.after(2000, actualizar_periodicamente)
                else:
                    print("🛑 Ventana de proyección cerrada, deteniendo actualizaciones")
                    self.timer_proyeccion = None
            except Exception as e:
                print(f"❌ Error en actualización periódica: {e}")
                self.timer_proyeccion = None
        
        # Iniciar el ciclo
        self.timer_proyeccion = self.root.after(2000, actualizar_periodicamente)

    def salir_pantalla_completa(self):
        if self.ventana_proyeccion and self.ventana_proyeccion.attributes('-fullscreen'):
            self.ventana_proyeccion.attributes('-fullscreen', False)
            monitor_idx = self.config_proyeccion.get("monitor", 0)
            if hasattr(self, 'monitores_detectados') and len(self.monitores_detectados) > monitor_idx:
                monitor = self.monitores_detectados[monitor_idx]
            else:
                monitor = {"x": 0, "y": 0, "width": 1920, "height": 1080}
            ancho = self.config_proyeccion["ancho"]
            alto = self.config_proyeccion["alto"]
            x = self.config_proyeccion["x"] + monitor["x"]
            y = self.config_proyeccion["y"] + monitor["y"]
            self.ventana_proyeccion.geometry(f"{ancho}x{alto}+{x}+{y}")
            self.crear_menu_controles_proyeccion()

    def crear_boton_flotante_pantalla_completa(self):
        if self.ventana_proyeccion and self.ventana_proyeccion.attributes('-fullscreen'):
            flotante_frame = tk.Frame(self.ventana_proyeccion, bg="black", relief="raised", borderwidth=1)
            flotante_frame.place(relx=0.98, rely=0.02, anchor="ne")
            tk.Button(flotante_frame,
                    text="✕ Salir Pant. Completa",
                    bg="#ff5252",
                    fg="white",
                    font=("Segoe UI", 9),
                    relief="flat",
                    padx=10,
                    pady=3,
                    cursor="hand2",
                    command=self.salir_pantalla_completa).pack(padx=5, pady=3)

    def crear_menu_controles_proyeccion(self):
        controles_frame = tk.Frame(self.ventana_proyeccion, bg="#333333")
        controles_frame.pack(fill="x", pady=(0, 5))
        tk.Button(controles_frame,
                 text="✕ Cerrar",
                 bg="#ff5252",
                 fg="white",
                 font=("Segoe UI", 9),
                 relief="flat",
                 padx=10,
                 pady=3,
                 cursor="hand2",
                 command=self.cerrar_proyeccion).pack(side="right", padx=5, pady=3)
        tk.Button(controles_frame,
                 text="💾 Guardar Posición",
                 bg="#4CAF50",
                 fg="white",
                 font=("Segoe UI", 9),
                 relief="flat",
                 padx=10,
                 pady=3,
                 cursor="hand2",
                 command=self.guardar_posicion_actual).pack(side="right", padx=5, pady=3)
        tk.Label(controles_frame,
                text="Arrastra para mover, borde para redimensionar",
                bg="#333333",
                fg="#AAAAAA",
                font=("Segoe UI", 8)).pack(side="left", padx=10, pady=3)

    def guardar_posicion_actual(self):
        if self.ventana_proyeccion and not self.ventana_proyeccion.attributes('-fullscreen'):
            try:
                geometry = self.ventana_proyeccion.geometry()
                partes = geometry.split('+')
                tamaño = partes[0].split('x')
                self.config_proyeccion["ancho"] = int(tamaño[0])
                self.config_proyeccion["alto"] = int(tamaño[1])
                self.config_proyeccion["x"] = int(partes[1])
                self.config_proyeccion["y"] = int(partes[2])
                guardar_config_proyeccion(self.config_proyeccion, self.db_config)
                if hasattr(self, 'proj_counter'):
                    mensaje = tk.Label(self.ventana_proyeccion,
                                      text="✓ Posición guardada",
                                      bg="#4CAF50",
                                      fg="white",
                                      font=("Segoe UI", 10))
                    mensaje.place(relx=0.5, rely=0.1, anchor="center")
                    self.ventana_proyeccion.after(2000, mensaje.destroy)
            except Exception as e:
                print(f"Error al guardar posición: {e}")

    def cerrar_proyeccion(self):
        """Cierra la ventana de proyección correctamente"""
        print("🔄 Cerrando ventana de proyección...")
        
        # Cancelar el timer de actualización
        if self.timer_proyeccion:
            try:
                self.root.after_cancel(self.timer_proyeccion)
            except:
                pass
            self.timer_proyeccion = None
        
        # Guardar posición si no está en pantalla completa
        if self.ventana_proyeccion and not self.ventana_proyeccion.attributes('-fullscreen'):
            self.guardar_posicion_actual()
        
        # Destruir la ventana
        if self.ventana_proyeccion:
            try:
                self.ventana_proyeccion.destroy()
            except:
                pass
        
        # Limpiar referencias
        self.ventana_proyeccion = None
        self.frame_tabla_proyeccion = None
        print("✅ Ventana de proyección cerrada")

    def actualizar_hora_proyeccion(self):
        if self.ventana_proyeccion and self.ventana_proyeccion.winfo_exists():
            ahora = datetime.now()
            self.hora_actual.config(text=ahora.strftime("%H:%M:%S"))
            self.fecha_actual.config(text=ahora.strftime("%d/%m/%Y"))
            self.ventana_proyeccion.after(1000, self.actualizar_hora_proyeccion)

    def actualizar_tabla_proyeccion(self):
        """Actualiza la tabla de la ventana de proyección"""
        # ✅ IMPORTANTE: Verificar que la ventana de proyección existe
        if not self.ventana_proyeccion or not self.ventana_proyeccion.winfo_exists():
            print("⚠️ Ventana de proyección no existe, cancelando actualización")
            return
            
        if not self.frame_tabla_proyeccion:
            return
            
        try:
            for widget in self.frame_tabla_proyeccion.winfo_children():
                widget.destroy()

            fondo_color = self.config_proyeccion.get("color_fondo", "black")
            texto_color = self.config_proyeccion.get("color_texto", "white")
            acento_color = self.config_proyeccion.get("color_acento", "#e94560")
            exito_color = self.config_proyeccion.get("color_exito", "#4CAF50")
            
            # Filtrar fallas según configuración
            fallas_a_mostrar = self.fallas_activas
            if not self.config_proyeccion.get("mostrar_pendientes", True):
                fallas_a_mostrar = [a for a in self.fallas_activas if a.get("estado") != "pendiente"]

            # ✅ Actualizar contador SOLO si existe y la ventana está viva
            if hasattr(self, 'proj_counter') and self.proj_counter and self.proj_counter.winfo_exists():
                if self.config_proyeccion.get("mostrar_contador", True):
                    self.proj_counter.config(text=str(len(fallas_a_mostrar)))
                else:
                    self.proj_counter.config(text="")

            if not fallas_a_mostrar:
                mensaje = "✅ No hay fallas activas"
                if not self.config_proyeccion.get("mostrar_pendientes", True) and any(a.get("estado") == "pendiente" for a in self.fallas_activas):
                    mensaje = "👁️ Mostrando solo fallas activas (pendientes ocultas)"
                
                no_data_label = tk.Label(self.frame_tabla_proyeccion,
                                    text=mensaje,
                                    bg=fondo_color,
                                    fg=exito_color,
                                    font=("Segoe UI", 24, "bold"))
                no_data_label.pack(expand=True)
                return

            columnas = ("#", "Máquina", "Tipo", "Inicio", "Proceso", "Fin", "Estado")
            
            # Calcular tamaño de fuente basado en el ancho de la ventana
            try:
                ancho = self.ventana_proyeccion.winfo_width()
                if ancho < 1000:
                    tamaño_fuente = 14
                    altura_fila = 40
                elif ancho < 1400:
                    tamaño_fuente = 18
                    altura_fila = 50
                else:
                    tamaño_fuente = 22
                    altura_fila = 60
            except:
                # Si hay error obteniendo el ancho, usar valores por defecto
                tamaño_fuente = 16
                altura_fila = 45

            tree = ttk.Treeview(
                self.frame_tabla_proyeccion,
                columns=columnas,
                show="headings"
            )

            style = ttk.Style()
            style.theme_use('clam')
            style.configure("Proyeccion.Treeview",
                            background=fondo_color,
                            foreground=texto_color,
                            rowheight=altura_fila,
                            fieldbackground=fondo_color,
                            borderwidth=0,
                            font=("Segoe UI", tamaño_fuente))
            style.configure("Proyeccion.Treeview.Heading",
                            background=acento_color,
                            foreground=texto_color,
                            relief="flat",
                            borderwidth=0,
                            font=("Segoe UI", tamaño_fuente + 2, "bold"))
            style.map('Proyeccion.Treeview',
                    background=[('selected', acento_color)],
                    foreground=[('selected', texto_color)])

            tree.configure(style="Proyeccion.Treeview")

            try:
                ancho_columna = int(self.frame_tabla_proyeccion.winfo_width() / 7)
            except:
                ancho_columna = 100  # Valor por defecto

            for col in columnas:
                tree.heading(col, text=col)
                tree.column(col, width=ancho_columna, anchor="center")

            scrollbar = ttk.Scrollbar(self.frame_tabla_proyeccion, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            tree.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            # Configurar colores para cada tipo
            tipos_unicos = set([alerta["tipo"] for alerta in fallas_a_mostrar])
            for tipo in tipos_unicos:
                color = self.get_color_for_tipo(tipo)
                text_color = self.get_text_color_for_background(color)
                tree.tag_configure(tipo,
                        background=color,
                        foreground=text_color,
                        font=("Segoe UI", tamaño_fuente, "bold"))
            
            # Configurar color para pendientes
            tree.tag_configure("pendiente", background=COLORES.get("pendiente", "#FFA500"))

            for alerta in fallas_a_mostrar:
                numero = alerta.get("numero_falla", "?")
                
                # ✅ USAR EL ESTADO GUARDADO DIRECTAMENTE
                estado_guardado = alerta.get("estado", "activa")
                
                # Determinar el texto a mostrar basado en el estado guardado
                if estado_guardado == "pendiente":
                    estado = "🟠 Pendiente"
                    tags = (alerta["tipo"], "pendiente")
                elif estado_guardado == "en_proceso":
                    estado = "🟡 En Proceso"
                    tags = (alerta["tipo"],)
                elif estado_guardado == "resuelta":
                    estado = "✅ Resuelta"
                    tags = (alerta["tipo"],)
                else:  # "activa" o cualquier otro
                    estado = "🔴 Activa"
                    tags = (alerta["tipo"],)

                def solo_hora(fecha):
                    try:
                        return datetime.strptime(fecha, "%Y-%m-%d %H:%M:%S").strftime("%H:%M:%S")
                    except:
                        return ""

                valores = (
                    f"#{numero}",
                    alerta["maquina"],
                    alerta["tipo"],
                    solo_hora(alerta.get("inicio", "")),
                    solo_hora(alerta.get("proceso", "")),
                    solo_hora(alerta.get("fin", "")),
                    estado
                )
                tree.insert("", "end", values=valores, tags=tags)

            # Bind para mostrar nota al hacer doble clic
            #tree.bind("<Double-1>", lambda e: self.mostrar_nota_proyeccion(e, tree))
            
        except Exception as e:
            print(f"Error al actualizar tabla de proyección: {e}")
            import traceback
            traceback.print_exc()
    
    def mostrar_nota_proyeccion(self, event, tree):
        """Muestra la nota de una falla pendiente desde la proyección"""
        item = tree.selection()[0]
        valores = tree.item(item, "values")
        tags = tree.item(item, "tags")
        
        # Buscar la falla correspondiente
        falla_encontrada = None
        for alerta in self.fallas_activas:
            if alerta["tipo"] == valores[2] and alerta["maquina"] == valores[1]:
                falla_encontrada = alerta
                break
        
        if falla_encontrada and "nota_pendiente" in falla_encontrada:
            self.mostrar_nota_pendiente(falla_encontrada)

    # ===== FUNCIONES DE ESTADÍSTICAS =====

    def mostrar_estadisticas(self):
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Estadísticas Avanzadas")
        stats_window.geometry("1000x800")  # Un poco más grande para los filtros
        stats_window.configure(bg=COLORES["fondo"])
        stats_window.resizable(True, True)

        stats_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (1000 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (800 // 2)
        stats_window.geometry(f"+{x}+{y}")

        # Frame superior para información y filtros
        top_frame = tk.Frame(stats_window, bg=COLORES["fondo"])
        top_frame.pack(fill="x", padx=20, pady=(20, 10))

        db_info = f"📊 Estadísticas Avanzadas - Base: {self.db_config['tipo'].upper()}"
        if self.db_config['tipo'] == 'mysql' and self.db_estado:
            db_info += f" ({self.db_config['host']})"
        
        tk.Label(top_frame, text=db_info, bg=COLORES["fondo"], 
                fg=COLORES["texto"], font=("Segoe UI", 18, "bold")).pack(anchor="w")

        # ===== FILTROS SOLO PARA PRO =====
        if hasattr(self, 'puede_ajustar_periodo_estadisticas') and self.puede_ajustar_periodo_estadisticas:
            filtros_frame = tk.Frame(top_frame, bg=COLORES["card"], relief="flat", bd=1)
            filtros_frame.pack(fill="x", pady=10)

            tk.Label(filtros_frame, text="🔍 Filtrar por período:", 
                    bg=COLORES["card"], fg=COLORES["texto"], 
                    font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15, pady=(10, 5))

            periodo_frame = tk.Frame(filtros_frame, bg=COLORES["card"])
            periodo_frame.pack(fill="x", padx=15, pady=5)

            tk.Label(periodo_frame, text="Desde:", bg=COLORES["card"], 
                    fg=COLORES["texto_secundario"], font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))
            
            self.stats_desde = DateEntry(periodo_frame, date_pattern='yyyy-mm-dd', width=12)
            self.stats_desde.pack(side="left", padx=(0, 20))

            tk.Label(periodo_frame, text="Hasta:", bg=COLORES["card"], 
                    fg=COLORES["texto_secundario"], font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))
            
            self.stats_hasta = DateEntry(periodo_frame, date_pattern='yyyy-mm-dd', width=12)
            self.stats_hasta.pack(side="left", padx=(0, 20))

            # Días para tendencia
            tk.Label(periodo_frame, text="Días tendencia:", bg=COLORES["card"], 
                    fg=COLORES["texto_secundario"], font=("Segoe UI", 10)).pack(side="left", padx=(20, 5))
            
            self.tendencia_dias_var = tk.StringVar(value=str(self.dias_tendencia_predeterminados))
            tk.Spinbox(periodo_frame, from_=1, to=90, textvariable=self.tendencia_dias_var,
                    width=5, bg="#2d3047", fg=COLORES["texto"], font=("Segoe UI", 10)).pack(side="left")

            tk.Button(periodo_frame, text="🔄 Aplicar Filtros", 
                    command=self.recargar_estadisticas_con_filtros,
                    bg=COLORES["accento"], fg=COLORES["texto"], font=("Segoe UI", 10),
                    relief="flat", padx=10, pady=2, cursor="hand2").pack(side="left", padx=20)

        notebook = ttk.Notebook(stats_window)
        notebook.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Crear las pestañas
        self.tab_resumen = ModernFrame(notebook)
        notebook.add(self.tab_resumen, text="📊 Resumen General")
        
        self.tab_tendencias = ModernFrame(notebook)
        notebook.add(self.tab_tendencias, text="📈 Tendencias")
        
        self.tab_metricas = ModernFrame(notebook)
        notebook.add(self.tab_metricas, text="🔧 Métricas por Tipo")
        
        self.tab_maquinas = ModernFrame(notebook)
        notebook.add(self.tab_maquinas, text="⚙️ Análisis de Máquinas")

        # Cargar datos iniciales
        self.recargar_estadisticas_con_filtros()
        
    def recargar_estadisticas_con_filtros(self):
        """Recarga todas las estadísticas aplicando los filtros de fecha (solo para PRO)"""
        
        # Determinar el período a usar
        if hasattr(self, 'puede_ajustar_periodo_estadisticas') and self.puede_ajustar_periodo_estadisticas:
            # Usar filtros seleccionados
            desde = self.stats_desde.get_date().strftime("%Y-%m-%d") if hasattr(self, 'stats_desde') else None
            hasta = self.stats_hasta.get_date().strftime("%Y-%m-%d") if hasattr(self, 'stats_hasta') else None
            dias_tendencia = int(self.tendencia_dias_var.get()) if hasattr(self, 'tendencia_dias_var') else 7
        else:
            # Usar valores por defecto (últimos 7 días)
            desde = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            hasta = datetime.now().strftime("%Y-%m-%d")
            dias_tendencia = 7

        # Recargar cada pestaña con los filtros
        self.mostrar_resumen_general(self.tab_resumen, desde, hasta)
        self.mostrar_tendencias(self.tab_tendencias, dias_tendencia)
        self.mostrar_metricas_por_tipo(self.tab_metricas, desde, hasta)
        self.mostrar_analisis_maquinas(self.tab_maquinas, desde, hasta)
    
    def mostrar_resumen_general(self, parent, fecha_desde=None, fecha_hasta=None):
        for widget in parent.winfo_children():
            widget.destroy()

        datos = None

        if self.db_config["tipo"] == "mysql" and self.db_estado:
            datos = self._obtener_resumen_mysql(fecha_desde, fecha_hasta)

        if datos is None:
            print("ℹ️ MySQL no disponible para resumen general ")
            return None
            

        self._crear_vista_resumen_general(parent, datos)

    def _obtener_resumen_mysql(self, fecha_desde=None, fecha_hasta=None):
        """Obtiene resumen general con filtros de fecha opcionales"""
        
        # ✅ Verificar disponibilidad primero
        if not self.mysql_disponible:
            print("ℹ️ MySQL no disponible para resumen")
            return None
    
        try:
            conn = self._conectar_mysql()  # ← USAR el método existente
            if not conn:
                print("❌ No se pudo conectar a MySQL")
                return None
            

            cursor = conn.cursor()
            
            # Construir condición de fecha
            condicion_fecha = ""
            params = []
            if fecha_desde and fecha_hasta:
                condicion_fecha = " WHERE DATE(inicio) BETWEEN %s AND %s"
                params = [fecha_desde, fecha_hasta]
            elif fecha_desde:
                condicion_fecha = " WHERE DATE(inicio) >= %s"
                params = [fecha_desde]
            elif fecha_hasta:
                condicion_fecha = " WHERE DATE(inicio) <= %s"
                params = [fecha_hasta]

            # Total de fallas en el período
            cursor.execute(f"SELECT COUNT(*) FROM fallas{condicion_fecha}", params)
            total_fallas = cursor.fetchone()[0] or 0

            # Fallas hoy (independiente del filtro)
            hoy = datetime.now().strftime("%Y-%m-%d")
            cursor.execute("SELECT COUNT(*) FROM fallas WHERE DATE(inicio) = %s", (hoy,))
            fallas_hoy = cursor.fetchone()[0] or 0

            # Máquinas afectadas en el período
            cursor.execute(f"SELECT COUNT(DISTINCT maquina) FROM fallas{condicion_fecha}", params)
            maquinas_afectadas = cursor.fetchone()[0] or 0

            # Tipo más común en el período
            cursor.execute(f"""
                SELECT tipo, COUNT(*) as cantidad
                FROM fallas
                {condicion_fecha}
                GROUP BY tipo
                ORDER BY cantidad DESC
                LIMIT 1
            """, params)
            tipo_result = cursor.fetchone()
            if tipo_result:
                tipo_mas_comun = tipo_result[0]
                cantidad_tipo_comun = tipo_result[1]
            else:
                tipo_mas_comun = "N/A"
                cantidad_tipo_comun = 0

            # Tiempo promedio en el período
            cursor.execute(f"""
                SELECT AVG(
                    CASE
                        WHEN fin IS NOT NULL
                        THEN TIMESTAMPDIFF(MINUTE, inicio, fin)
                        ELSE NULL
                    END
                ) as promedio
                FROM fallas
                {condicion_fecha}
            """, params)
            promedio = cursor.fetchone()[0]
            tiempo_promedio = promedio if promedio is not None else 0

            conn.close()

            print(f"✅ Datos obtenidos de MySQL para resumen general (período: {fecha_desde} - {fecha_hasta})")
            return {
                "total_fallas": total_fallas,
                "fallas_hoy": fallas_hoy,
                "maquinas_afectadas": maquinas_afectadas,
                "tipo_mas_comun": tipo_mas_comun,
                "cantidad_tipo_comun": cantidad_tipo_comun,
                "tiempo_promedio": tiempo_promedio,
                "fuente": "MySQL"
            }

        except Exception as e:
            print(f"❌ Error obteniendo resumen de MySQL: {e}")
            return None
    
    
    def _crear_vista_resumen_general(self, parent, datos):
        main_frame = tk.Frame(parent, bg=COLORES["fondo"])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        fuente_text = f"📊 Resumen General de Fallas - Fuente: {datos.get('fuente', 'Desconocida')}"
        tk.Label(main_frame,
                text=fuente_text,
                bg=COLORES["fondo"],
                fg=COLORES["texto"],
                font=("Segoe UI", 16, "bold")).pack(pady=(0, 30))

        stats_grid = tk.Frame(main_frame, bg=COLORES["fondo"])
        stats_grid.pack(fill="x")

        stats_grid.columnconfigure(0, weight=1)
        stats_grid.columnconfigure(1, weight=1)

        stat_items = [
            ("📊 Total de Fallas", datos["total_fallas"]),
            ("📅 Fallas Hoy", datos["fallas_hoy"]),
            ("🔧 Máquinas Afectadas", datos["maquinas_afectadas"]),
            ("⏱️ Tiempo Promedio", f"{datos['tiempo_promedio']:.1f} min"),
        ]

        for i, (label, value) in enumerate(stat_items):
            row = i // 2
            col = i % 2

            card = tk.Frame(stats_grid, bg=COLORES["card"], relief="ridge", bd=2)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

            tk.Label(card,
                    text=label,
                    bg=COLORES["card"],
                    fg=COLORES["texto_secundario"],
                    font=("Segoe UI", 12)).pack(pady=(20, 10))

            tk.Label(card,
                    text=str(value),
                    bg=COLORES["card"],
                    fg=COLORES["accento"],
                    font=("Segoe UI", 24, "bold")).pack(pady=(0, 20))

        tipo_card = tk.Frame(main_frame, bg=COLORES["card"], relief="ridge", bd=2)
        tipo_card.pack(fill="x", padx=10, pady=20)

        tk.Label(tipo_card,
                text="🏆 Tipo de Falla Más Común",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 14, "bold")).pack(pady=(15, 10))

        tipo_frame = tk.Frame(tipo_card, bg=COLORES["card"])
        tipo_frame.pack(pady=(0, 20))

        color = self.get_color_for_tipo(datos["tipo_mas_comun"])
        tk.Label(tipo_frame,
                text=datos["tipo_mas_comun"],
                bg=color,
                fg="#000000" if self.is_light_color(color) else "#FFFFFF",
                font=("Segoe UI", 18, "bold"),
                padx=30,
                pady=10).pack(side="left", padx=10)

        tk.Label(tipo_frame,
                text=f"({datos['cantidad_tipo_comun']} ocurrencias)",
                bg=COLORES["card"],
                fg=COLORES["texto_secundario"],
                font=("Segoe UI", 14)).pack(side="left", padx=10)

    def mostrar_tendencias(self, parent, dias=7):
        """Muestra las tendencias para los últimos N días"""
        for widget in parent.winfo_children():
            widget.destroy()

        datos = None

        if self.db_config["tipo"] == "mysql" and self.db_estado:
            datos = self._obtener_tendencias_mysql(dias)

        if datos is None:
            print("ℹ️ MySQL no disponible para mostrar tendencias")
            return None

        if datos:
            self._crear_grafica_tendencias(parent, datos)
        else:
            tk.Label(parent,
                    text="No hay datos de tendencias disponibles",
                    bg=COLORES["fondo"],
                    fg=COLORES["texto_secundario"],
                    font=("Segoe UI", 14)).pack(pady=50)
        
    def _obtener_tendencias_mysql(self, dias=7):
        """Obtiene datos de tendencia para los últimos N días"""
        
        # ✅ Verificar disponibilidad primero
        if not self.mysql_disponible:
            print("ℹ️ MySQL no disponible para tendencias")
            return None
    
        try:
            conn = self._conectar_mysql()  # ← USAR el método existente
            if not conn:
                print("❌ No se pudo conectar a MySQL")
                return None

            cursor = conn.cursor()
            datos = []

            for i in range(dias - 1, -1, -1):
                fecha = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                cursor.execute("SELECT COUNT(*) FROM fallas WHERE DATE(inicio) = %s", (fecha,))
                count = cursor.fetchone()[0] or 0
                datos.append((fecha, count))

            conn.close()
            print(f"✅ Datos de tendencias obtenidos de MySQL ({dias} días)")
            return datos

        except Exception as e:
            print(f"❌ Error obteniendo tendencias de MySQL: {e}")
            return None
    
    def _crear_grafica_tendencias(self, parent, datos):
        fig, ax = plt.subplots(figsize=(10, 6))
        fechas = [d[0][5:] for d in datos]
        valores = [d[1] for d in datos]

        ax.bar(fechas, valores, color=COLORES["accento"])
        ax.set_title("Fallas en los Últimos 7 Días", fontsize=14, fontweight='bold')
        ax.set_xlabel("Fecha")
        ax.set_ylabel("Número de Fallas")
        ax.tick_params(axis='x', rotation=45)

        for i, v in enumerate(valores):
            ax.text(i, v + 0.1, str(v), ha='center', va='bottom', fontweight='bold')

        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=20)

    def mostrar_metricas_por_tipo(self, parent, fecha_desde=None, fecha_hasta=None):
        """Muestra métricas por tipo con filtros de fecha opcionales"""
        for widget in parent.winfo_children():
            widget.destroy()

        tk.Label(parent,
                text="Métricas Detalladas por Tipo de Falla",
                bg=COLORES["fondo"],
                fg=COLORES["texto"],
                font=("Segoe UI", 14, "bold")).pack(pady=20)

        canvas = tk.Canvas(parent, bg=COLORES["fondo"], highlightthickness=0)
        scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ModernFrame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        if self.db_config["tipo"] == "mysql" and self.db_estado:
            exito = self._mostrar_metricas_mysql(scrollable_frame, fecha_desde, fecha_hasta)
            if not exito:
                print("ℹ️ MySQL no disponible para mostrar metricas por ttipo")
                return False
                

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _mostrar_metricas_mysql(self, scrollable_frame, fecha_desde=None, fecha_hasta=None):
        
        # ✅ Verificar disponibilidad primero
        if not self.mysql_disponible:
            print("ℹ️ MySQL no disponible para métricas")
            return False
    
        """Muestra métricas por tipo con filtros de fecha opcionales"""
        try:
            conn = self._conectar_mysql()  # ← USAR el método existente
            if not conn:
                print("❌ No se pudo conectar a MySQL")
                return False

            cursor = conn.cursor()
            
            # Construir condición de fecha
            condicion_fecha = ""
            params = []
            if fecha_desde and fecha_hasta:
                condicion_fecha = " WHERE DATE(inicio) BETWEEN %s AND %s"
                params = [fecha_desde, fecha_hasta]
            elif fecha_desde:
                condicion_fecha = " WHERE DATE(inicio) >= %s"
                params = [fecha_desde]
            elif fecha_hasta:
                condicion_fecha = " WHERE DATE(inicio) <= %s"
                params = [fecha_hasta]

            # Obtener tipos distintos
            cursor.execute(f"SELECT DISTINCT tipo FROM fallas{condicion_fecha}", params)
            tipos_bd = [row[0] for row in cursor.fetchall()]

            tipos_a_mostrar = tipos_bd if tipos_bd else self.tipos_falla

            for tipo in tipos_a_mostrar:
                params_tipo = params + [tipo] if params else [tipo]
                condicion_con_tipo = condicion_fecha + " AND tipo = %s" if condicion_fecha else " WHERE tipo = %s"
                
                cursor.execute(f"SELECT COUNT(*) FROM fallas{condicion_con_tipo}", params_tipo)
                total = cursor.fetchone()[0] or 0

                cursor.execute(f"""
                    SELECT AVG(
                        CASE
                            WHEN fin IS NOT NULL
                            THEN TIMESTAMPDIFF(MINUTE, inicio, fin)
                            ELSE NULL
                        END
                    ) as promedio
                    FROM fallas
                    {condicion_con_tipo}
                """, params_tipo)
                promedio = cursor.fetchone()[0]

                self._crear_frame_metrica_tipo(scrollable_frame, tipo, total, promedio)

            conn.close()
            print(f"✅ Métricas por tipo obtenidas de MySQL (período: {fecha_desde} - {fecha_hasta})")
            return True

        except Exception as e:
            print(f"❌ Error en MySQL para métricas por tipo: {e}")
            return False
    
    
    def _crear_frame_metrica_tipo(self, parent, tipo, total, tiempo_promedio):
        tipo_frame = tk.Frame(parent, bg=COLORES["card"])
        tipo_frame.pack(fill="x", padx=20, pady=5)

        color = self.get_color_for_tipo(tipo)

        tk.Label(tipo_frame,
                text=tipo,
                bg=color,
                fg="#000000" if self.is_light_color(color) else "#FFFFFF",
                font=("Segoe UI", 10, "bold"),
                width=15,
                anchor="center").pack(side="left", padx=10, pady=10)

        tiempo_text = f" | Tiempo Promedio: {tiempo_promedio:.1f} min" if tiempo_promedio is not None else ""
        tk.Label(tipo_frame,
                text=f"Total: {total}{tiempo_text}",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 10)
        ).pack(side="left", padx=10, pady=10)

    def _conectar_mysql(self, timeout=2):
        """Intenta conectar a MySQL con timeout reducido"""
        try:
            conn = mysql.connector.connect(
                host=self.db_config["host"],
                port=self.db_config["port"],
                user=self.db_config["usuario"],
                password=self.db_config["password"],
                database=self.db_config["base_datos"],
                connection_timeout=timeout,
                ssl_disabled=not self.db_config["usar_ssl"],
                use_pure=True,
                autocommit=False,
                buffered=True
            )
            return conn
        except mysql.connector.Error as e:
            print(f"⚠️ MySQL no disponible: {e}")
            return None
        except Exception as e:
            print(f"⚠️ Error inesperado MySQL: {e}")
            return None
    
    def mostrar_analisis_maquinas(self, parent, fecha_desde=None, fecha_hasta=None):
        """Muestra análisis de máquinas con filtros de fecha opcionales"""
        for widget in parent.winfo_children():
            widget.destroy()

        canvas = tk.Canvas(parent, bg=COLORES["fondo"], highlightthickness=0)
        scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ModernFrame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        tk.Label(scrollable_frame,
                text="Top 10 Máquinas con Más Fallas - Desglose por Tipo",
                bg=COLORES["fondo"],
                fg=COLORES["texto"],
                font=("Segoe UI", 16, "bold")).pack(pady=(20, 30))

        if self.db_config["tipo"] == "mysql" and self.db_estado:
            exito = self._mostrar_analisis_maquinas_mysql(scrollable_frame, fecha_desde, fecha_hasta)
            if not exito:
                print("⚠️ MySQL falló, mostrar_analisis_maquinas")

        tk.Button(scrollable_frame,
                text="📊 Exportar Análisis de Máquinas",
                bg=COLORES["accento"],
                fg=COLORES["texto"],
                font=("Segoe UI", 11, "bold"),
                relief="flat",
                padx=20,
                pady=10,
                cursor="hand2",
                command=lambda: self.exportar_analisis_maquinas(fecha_desde, fecha_hasta)).pack(pady=30)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _mostrar_analisis_maquinas_mysql(self, scrollable_frame, fecha_desde=None, fecha_hasta=None):
        """Muestra análisis de máquinas con filtros de fecha opcionales"""
        
        # ✅ Verificar disponibilidad primero
        if not self.mysql_disponible:
            print("ℹ️ MySQL no disponible para análisis de máquinas")
            return False
    
        try:
            conn = self._conectar_mysql()  # ← USAR el método existente
            if not conn:
                print("❌ No se pudo conectar a MySQL")
                return False

            cursor = conn.cursor()
            
            # Construir condición de fecha
            condicion_fecha = ""
            params = []
            if fecha_desde and fecha_hasta:
                condicion_fecha = " WHERE DATE(inicio) BETWEEN %s AND %s"
                params = [fecha_desde, fecha_hasta]
            elif fecha_desde:
                condicion_fecha = " WHERE DATE(inicio) >= %s"
                params = [fecha_desde]
            elif fecha_hasta:
                condicion_fecha = " WHERE DATE(inicio) <= %s"
                params = [fecha_hasta]

            cursor.execute(f"""
                SELECT maquina, COUNT(*) as total
                FROM fallas
                {condicion_fecha}
                GROUP BY maquina
                ORDER BY total DESC
                LIMIT 10
            """, params)
            top_maquinas = cursor.fetchall()

            if not top_maquinas:
                conn.close()
                return False

            for idx, maquina_data in enumerate(top_maquinas, 1):
                maquina = maquina_data[0]
                total = maquina_data[1]

                maquina_container = self._crear_contenedor_maquina(scrollable_frame, idx, maquina, total)

                # Para el desglose por tipo, necesitamos la misma condición de fecha
                params_tipo = params + [maquina] if params else [maquina]
                condicion_tipo = condicion_fecha + " AND maquina = %s" if condicion_fecha else " WHERE maquina = %s"
                
                cursor.execute(f"""
                    SELECT tipo, COUNT(*) as cantidad
                    FROM fallas
                    {condicion_tipo}
                    GROUP BY tipo
                    ORDER BY cantidad DESC
                """, params_tipo)
                tipos_maquina = cursor.fetchall()

                self._crear_desglose_maquina(maquina_container, tipos_maquina, total)

            conn.close()
            print(f"✅ Análisis de máquinas obtenido de MySQL (período: {fecha_desde} - {fecha_hasta})")
            return True

        except Exception as e:
            print(f"❌ Error en MySQL para análisis de máquinas: {e}")
            return False
    
    def _crear_contenedor_maquina(self, parent, idx, maquina, total):
        maquina_container = tk.Frame(parent, bg=COLORES["card"],
                                    relief="ridge", bd=2)
        maquina_container.pack(fill="x", padx=20, pady=10)

        header_frame = tk.Frame(maquina_container, bg=COLORES["card"])
        header_frame.pack(fill="x", padx=15, pady=10)

        tk.Label(header_frame,
                text=f"#{idx} - Máquina {maquina}",
                bg=COLORES["card"],
                fg=COLORES["accento"],
                font=("Segoe UI", 14, "bold")).pack(side="left")

        tk.Label(header_frame,
                text=f"Total: {total} fallas",
                bg=COLORES["card"],
                fg=COLORES["success"],
                font=("Segoe UI", 12, "bold")).pack(side="right")

        tk.Frame(maquina_container, bg=COLORES["texto_secundario"], height=1).pack(fill="x", padx=15, pady=5)

        return maquina_container

    def _crear_desglose_maquina(self, container, tipos_maquina, total):
        desglose_frame = tk.Frame(container, bg=COLORES["card"])
        desglose_frame.pack(fill="x", padx=25, pady=15)

        headers_frame = tk.Frame(desglose_frame, bg=self.lighten_color(COLORES["card"], -0.1))
        headers_frame.pack(fill="x", pady=(0, 5))

        tk.Label(headers_frame,
                text="Tipo de Falla",
                bg=self.lighten_color(COLORES["card"], -0.1),
                fg=COLORES["texto"],
                font=("Segoe UI", 10, "bold"),
                width=25,
                anchor="w").pack(side="left", padx=10, pady=5)

        tk.Label(headers_frame,
                text="Cantidad",
                bg=self.lighten_color(COLORES["card"], -0.1),
                fg=COLORES["texto"],
                font=("Segoe UI", 10, "bold"),
                width=15,
                anchor="center").pack(side="left", padx=10, pady=5)

        tk.Label(headers_frame,
                text="Porcentaje",
                bg=self.lighten_color(COLORES["card"], -0.1),
                fg=COLORES["texto"],
                font=("Segoe UI", 10, "bold"),
                width=15,
                anchor="center").pack(side="left", padx=10, pady=5)

        for tipo_data in tipos_maquina:
            if isinstance(tipo_data, dict):
                tipo = tipo_data['tipo']
                cantidad = tipo_data['cantidad']
            else:
                tipo = tipo_data[0]
                cantidad = tipo_data[1]

            row_frame = tk.Frame(desglose_frame, bg=COLORES["card"])
            row_frame.pack(fill="x", pady=2)

            color_indicador = tk.Frame(row_frame,
                                    bg=self.get_color_for_tipo(tipo),
                                    width=15, height=15)
            color_indicador.pack(side="left", padx=(5, 10))
            color_indicador.pack_propagate(False)

            tk.Label(row_frame,
                    text=tipo,
                    bg=COLORES["card"],
                    fg=COLORES["texto"],
                    font=("Segoe UI", 10),
                    width=23,
                    anchor="w").pack(side="left", padx=5)

            tk.Label(row_frame,
                    text=str(cantidad),
                    bg=COLORES["card"],
                    fg=COLORES["texto"],
                    font=("Segoe UI", 10, "bold"),
                    width=15,
                    anchor="center").pack(side="left", padx=5)

            porcentaje = (cantidad / total) * 100
            tk.Label(row_frame,
                    text=f"{porcentaje:.1f}%",
                    bg=COLORES["card"],
                    fg=COLORES["warning"],
                    font=("Segoe UI", 10),
                    width=15,
                    anchor="center").pack(side="left", padx=5)

            barra_frame = tk.Frame(row_frame, bg=COLORES["fondo"], width=100, height=10)
            barra_frame.pack(side="left", padx=10)
            barra_frame.pack_propagate(False)

            barra_progreso = tk.Frame(barra_frame,
                                    bg=self.get_color_for_tipo(tipo),
                                    width=int(porcentaje),
                                    height=10)
            barra_progreso.pack(side="left")

    def exportar_analisis_maquinas(self, fecha_desde=None, fecha_hasta=None):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            initialfile="analisis_maquinas.xlsx"
        )

        if not file_path:
            return

        try:
            # Construir condición de fecha
            condicion_fecha = ""
            params = []
            if fecha_desde and fecha_hasta:
                condicion_fecha = " WHERE DATE(inicio) BETWEEN %s AND %s" if self.db_config["tipo"] == "mysql" else " WHERE date(inicio) BETWEEN ? AND ?"
                params = [fecha_desde, fecha_hasta]
            elif fecha_desde:
                condicion_fecha = " WHERE DATE(inicio) >= %s" if self.db_config["tipo"] == "mysql" else " WHERE date(inicio) >= ?"
                params = [fecha_desde]
            elif fecha_hasta:
                condicion_fecha = " WHERE DATE(inicio) <= %s" if self.db_config["tipo"] == "mysql" else " WHERE date(inicio) <= ?"
                params = [fecha_hasta]

            if self.db_config["tipo"] == "mysql" and self.db_estado:
                import mysql.connector
                conn = mysql.connector.connect(
                    host=self.db_config["host"],
                    port=self.db_config["port"],
                    user=self.db_config["usuario"],
                    password=self.db_config["password"],
                    database=self.db_config["base_datos"],
                    connection_timeout=self.db_config["timeout"],
                    ssl_disabled=not self.db_config["usar_ssl"]
                )

                query_resumen = f"""
                    SELECT
                        maquina,
                        COUNT(*) as total_fallas,
                        COUNT(DISTINCT tipo) as tipos_distintos,
                        MIN(DATE(inicio)) as primera_falla,
                        MAX(DATE(inicio)) as ultima_falla
                    FROM fallas
                    {condicion_fecha}
                    GROUP BY maquina
                    ORDER BY total_fallas DESC
                """
                df_resumen = pd.read_sql_query(query_resumen, conn, params=params)

                query_detalle = f"""
                    SELECT
                        maquina,
                        tipo,
                        COUNT(*) as cantidad,
                        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY maquina), 1) as porcentaje
                    FROM fallas
                    {condicion_fecha}
                    GROUP BY maquina, tipo
                    ORDER BY maquina, cantidad DESC
                """
                df_detalle = pd.read_sql_query(query_detalle, conn, params=params)

                conn.close()
            

            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df_resumen.to_excel(writer, sheet_name='Resumen por Máquina', index=False)
                df_detalle.to_excel(writer, sheet_name='Desglose por Tipo', index=False)

            messagebox.showinfo("Éxito", f"Análisis de máquinas exportado a:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar el análisis:\n{str(e)}")
        
    def mostrar_configuracion(self):
        if not self.puede_configurar:
            messagebox.showinfo("Acceso Restringido",
                            "La configuración no está disponible\n"
                            "con tu licencia actual.\n\n"
                            "Actualiza a una licencia MID o PRO para acceder.")
            return

        if len(self.tipos_falla) > self.max_tipos_falla:
            self.tipos_falla = self.tipos_falla[:self.max_tipos_falla]
            COLORES["fallas"] = self.tipos_falla
            self.actualizar_comboboxes_tipos()
            print(f"⚠️ Tipos de falla recortados a {self.max_tipos_falla} según licencia al abrir configuración.")

        if hasattr(self, 'config_window') and self.config_window and self.config_window.winfo_exists():
            self.config_window.lift()
            self.config_window.focus_force()
            return

        config_window = tk.Toplevel(self.root)
        config_window.title("Configuración del Sistema")
        config_window.geometry("800x900")
        config_window.configure(bg=COLORES["fondo"])
        config_window.resizable(True, True)
        config_window.minsize(700, 700)

        config_window.transient(self.root)
        config_window.grab_set()

        config_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (800 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (900 // 2)
        config_window.geometry(f"+{x}+{y}")

        self.config_window = config_window

        main_container = tk.Frame(config_window, bg=COLORES["fondo"])
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(main_container,
                text="⚙️ Configuración del Sistema",
                bg=COLORES["fondo"],
                fg=COLORES["texto"],
                font=("Segoe UI", 18, "bold")).pack(pady=(0, 20))

        canvas_frame = tk.Frame(main_container, bg=COLORES["fondo"])
        canvas_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(canvas_frame, bg=COLORES["fondo"], highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORES["fondo"])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # --- CONFIGURACIÓN DE BASE DE DATOS ---
        db_card = tk.Frame(scrollable_frame, bg=COLORES["card"], relief="flat", bd=1,
                        highlightbackground=COLORES["texto_secundario"])
        db_card.pack(fill="x", padx=10, pady=(0, 15))

        tk.Label(db_card,
                text="💾 Configuración de Base de Datos",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=15, pady=(15, 10))

        tipo_frame = tk.Frame(db_card, bg=COLORES["card"])
        tipo_frame.pack(fill="x", padx=15, pady=5)

        tk.Label(tipo_frame,
                    text="Tipo de BD: MySQL (obligatorio)",
                    bg=COLORES["card"],
                    fg=COLORES["texto"],
                    font=("Segoe UI", 11, "bold"),
                    width=15,
                    anchor="w").pack(side="left")

        tk.Label(tipo_frame,
                text="MySQL",
                bg=COLORES["success"],
                fg="white",
                font=("Segoe UI", 10, "bold"),
                padx=10,
                pady=2).pack(side="left", padx=5)

        # Variable para el tipo de BD (simplificada, siempre MySQL)
        self.db_tipo_var = tk.StringVar(value="mysql")

        self.mysql_frame = tk.Frame(db_card, bg=COLORES["card"])
        self.mysql_frame.pack(fill="x", padx=15, pady=10)

        host_frame = tk.Frame(self.mysql_frame, bg=COLORES["card"])
        host_frame.pack(fill="x", pady=5)

        tk.Label(host_frame,
                text="Host:",
                bg=COLORES["card"],
                fg=COLORES["texto_secundario"],
                font=("Segoe UI", 10),
                width=15,
                anchor="w").pack(side="left")

        self.db_host_var = tk.StringVar(value=self.db_config["host"])
        entry_host = tk.Entry(host_frame,
                textvariable=self.db_host_var,
                width=25,
                bg=COLORES.get("superficie3", "#2d3047"),  # ← USA EL COLOR DEL TEMA
                fg=COLORES["texto"],
                relief="flat",
                font=("Segoe UI", 10))
        entry_host.pack(side="left", padx=5)

        puerto_frame = tk.Frame(self.mysql_frame, bg=COLORES["card"])
        puerto_frame.pack(fill="x", pady=5)

        tk.Label(puerto_frame,
                text="Puerto:",
                bg=COLORES["card"],
                fg=COLORES["texto_secundario"],
                font=("Segoe UI", 10),
                width=15,
                anchor="w").pack(side="left")

        self.db_port_var = tk.StringVar(value=str(self.db_config["port"]))
        entry_port = tk.Entry(puerto_frame,
                textvariable=self.db_port_var,
                width=10,
                bg=COLORES.get("superficie3", "#2d3047"),
                fg=COLORES["texto"],
                relief="flat",
                font=("Segoe UI", 10))
        entry_port.pack(side="left", padx=5)

        user_frame = tk.Frame(self.mysql_frame, bg=COLORES["card"])
        user_frame.pack(fill="x", pady=5)

        tk.Label(user_frame,
                text="Usuario:",
                bg=COLORES["card"],
                fg=COLORES["texto_secundario"],
                font=("Segoe UI", 10),
                width=15,
                anchor="w").pack(side="left")

        self.db_user_var = tk.StringVar(value=self.db_config["usuario"])
        entry_user = tk.Entry(user_frame,
                textvariable=self.db_user_var,
                width=25,
                bg=COLORES.get("superficie3", "#2d3047"),
                fg=COLORES["texto"],
                relief="flat",
                font=("Segoe UI", 10))
        entry_user.pack(side="left", padx=5)

        pass_frame = tk.Frame(self.mysql_frame, bg=COLORES["card"])
        pass_frame.pack(fill="x", pady=5)

        tk.Label(pass_frame,
                text="Contraseña:",
                bg=COLORES["card"],
                fg=COLORES["texto_secundario"],
                font=("Segoe UI", 10),
                width=15,
                anchor="w").pack(side="left")

        self.db_pass_var = tk.StringVar(value=self.db_config["password"])
        entry_pass = tk.Entry(pass_frame,
                textvariable=self.db_pass_var,
                width=25,
                bg=COLORES.get("superficie3", "#2d3047"),
                fg=COLORES["texto"],
                show="•",
                relief="flat",
                font=("Segoe UI", 10))
        entry_pass.pack(side="left", padx=5)

        dbname_frame = tk.Frame(self.mysql_frame, bg=COLORES["card"])
        dbname_frame.pack(fill="x", pady=5)

        tk.Label(dbname_frame,
                text="Base de Datos:",
                bg=COLORES["card"],
                fg=COLORES["texto_secundario"],
                font=("Segoe UI", 10),
                width=15,
                anchor="w").pack(side="left")

        self.db_name_var = tk.StringVar(value=self.db_config["base_datos"])
        entry_dbname = tk.Entry(dbname_frame,
                textvariable=self.db_name_var,
                width=25,
                bg=COLORES.get("superficie3", "#2d3047"),
                fg=COLORES["texto"],
                relief="flat",
                font=("Segoe UI", 10))
        entry_dbname.pack(side="left", padx=5)

        timeout_frame = tk.Frame(self.mysql_frame, bg=COLORES["card"])
        timeout_frame.pack(fill="x", pady=5)

        tk.Label(timeout_frame,
                text="Timeout (seg):",
                bg=COLORES["card"],
                fg=COLORES["texto_secundario"],
                font=("Segoe UI", 10),
                width=15,
                anchor="w").pack(side="left")

        self.db_timeout_var = tk.StringVar(value=str(self.db_config["timeout"]))
        entry_timeout = tk.Entry(timeout_frame,
                textvariable=self.db_timeout_var,
                width=10,
                bg=COLORES.get("superficie3", "#2d3047"),
                fg=COLORES["texto"],
                relief="flat",
                font=("Segoe UI", 10))
        entry_timeout.pack(side="left", padx=5)

        ssl_frame = tk.Frame(self.mysql_frame, bg=COLORES["card"])
        ssl_frame.pack(fill="x", pady=5)

        self.db_ssl_var = tk.BooleanVar(value=self.db_config["usar_ssl"])
        cb_ssl = tk.Checkbutton(ssl_frame,
                    text="Usar SSL",
                    variable=self.db_ssl_var,
                    bg=COLORES["card"],
                    fg=COLORES["texto"],
                    selectcolor=COLORES["accento"],
                    font=("Segoe UI", 10))
        cb_ssl.pack(anchor="w", padx=20)

        db_buttons_frame = tk.Frame(self.mysql_frame, bg=COLORES["card"])
        db_buttons_frame.pack(fill="x", pady=15)

        btn_probar = tk.Button(db_buttons_frame,
                text="🔌 Probar Conexión",
                bg=COLORES["success"],
                fg=COLORES["texto"],
                font=("Segoe UI", 10),
                relief="flat",
                padx=15,
                pady=5,
                cursor="hand2",
                command=self.probar_conexion_bd)
        btn_probar.pack(side="left", padx=5)

        btn_inicializar = tk.Button(db_buttons_frame,
                text="🔄 Inicializar BD",
                bg=COLORES["warning"],
                fg=COLORES["negro"],
                font=("Segoe UI", 10),
                relief="flat",
                padx=15,
                pady=5,
                cursor="hand2",
                command=self.inicializar_bd_desde_config)
        btn_inicializar.pack(side="left", padx=5)

        self.db_estado_label = tk.Label(self.mysql_frame,
                                    text="",
                                    bg=COLORES["card"],
                                    fg=COLORES["texto"],
                                    font=("Segoe UI", 9))
        self.db_estado_label.pack(anchor="w", padx=15, pady=5)

        def actualizar_visibilidad_mysql(*args):
            if self.db_tipo_var.get() == "mysql" and self.puede_usar_mysql:
                self.mysql_frame.pack(fill="x", padx=15, pady=10)
            else:
                self.mysql_frame.pack_forget()

        self.db_tipo_var.trace_add("write", actualizar_visibilidad_mysql)
        actualizar_visibilidad_mysql()

        # --- NOMBRE DEL SISTEMA ---
        nombre_card = tk.Frame(scrollable_frame, bg=COLORES["card"], relief="flat", bd=1,
                            highlightbackground=COLORES["texto_secundario"])
        nombre_card.pack(fill="x", padx=10, pady=(0, 15))

        tk.Label(nombre_card,
                text="Nombre del Sistema:",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15, pady=(15, 5))

        nombre_frame = tk.Frame(nombre_card, bg=COLORES["card"])
        nombre_frame.pack(fill="x", padx=15, pady=(0, 15))

        self.entry_nombre = ModernEntry(nombre_frame, width=30)
        self.entry_nombre.insert(0, self.nombre_sistema)
        self.entry_nombre.pack(side="left", padx=(0, 10))

        tk.Button(nombre_frame,
                text="Cambiar",
                bg=COLORES["accento"],
                fg=COLORES["texto"],
                font=("Segoe UI", 10),
                relief="flat",
                padx=15,
                pady=5,
                cursor="hand2",
                command=self.cambiar_nombre_sistema).pack(side="left")

        # --- TIPOS DE FALLA ---
        tipos_card = tk.Frame(scrollable_frame, bg=COLORES["card"], relief="flat", bd=1,
                            highlightbackground=COLORES["texto_secundario"])
        tipos_card.pack(fill="x", padx=10, pady=(0, 15))

        limite_frame = tk.Frame(tipos_card, bg=COLORES["card"])
        limite_frame.pack(fill="x", padx=15, pady=(10, 0))
        
        mapeo_card = tk.Frame(scrollable_frame, bg=COLORES["card"], relief="flat", bd=1,
                            highlightbackground=COLORES["texto_secundario"])
        mapeo_card.pack(fill="x", padx=10, pady=(0, 15))

        tk.Label(mapeo_card,
                text="🔌 Configuración de Botones Físicos",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=15, pady=(15, 10))

        tk.Label(mapeo_card,
                text="Asigna cada botón físico a un tipo de falla:",
                bg=COLORES["card"],
                fg=COLORES["texto_secundario"],
                font=("Segoe UI", 10)).pack(anchor="w", padx=15, pady=(0, 10))

        # Frame para los comboboxes de mapeo
        mapeo_frame = tk.Frame(mapeo_card, bg=COLORES["card"])
        mapeo_frame.pack(fill="x", padx=15, pady=5)

        # Crear variables para guardar las selecciones
        self.mapeo_vars = {}  # Diccionario {numero_boton: variable tk.StringVar}

        # Crear filas para botones del 1 al 5 (puedes ajustar el rango)
        for i in range(1, 6):  # Botones 1 a 5
            row_frame = tk.Frame(mapeo_frame, bg=COLORES["card"])
            row_frame.pack(fill="x", pady=3)
            
            # Etiqueta del botón
            tk.Label(row_frame,
                    text=f"Botón {i}:",
                    bg=COLORES["card"],
                    fg=COLORES["texto"],
                    font=("Segoe UI", 10, "bold"),
                    width=10,
                    anchor="w").pack(side="left", padx=(0, 10))
            
            # Combobox para seleccionar tipo de falla
            var = tk.StringVar()
            # Si ya hay un mapeo guardado, establecerlo
            if i in self.mapeo_botones:
                var.set(self.mapeo_botones[i])
            
            combo = ttk.Combobox(row_frame, 
                                textvariable=var, 
                                values=self.tipos_falla,
                                width=25,
                                state="readonly")
            combo.pack(side="left", padx=5)
            
            # Guardar la variable
            self.mapeo_vars[i] = var

        # Botón para guardar el mapeo (opcional, se guardará junto con la config general)
        info_label = tk.Label(mapeo_card,
                            text="Nota: El mapeo se guardará cuando presiones 'Guardar Configuración'",
                            bg=COLORES["card"],
                            fg=COLORES["warning"],
                            font=("Segoe UI", 9, "italic"))
        info_label.pack(anchor="w", padx=15, pady=(10, 15))

        tk.Label(limite_frame,
                text=f"📊 Tipos de falla permitidos: {len(self.tipos_falla)}/{self.max_tipos_falla}",
                bg=COLORES["card"],
                fg=COLORES["success"] if len(self.tipos_falla) < self.max_tipos_falla else COLORES["danger"],
                font=("Segoe UI", 11, "bold")).pack(anchor="w")

        if len(self.tipos_falla) >= self.max_tipos_falla:
            tk.Label(limite_frame,
                    text="⚠️ Has alcanzado el límite máximo. Elimina algún tipo para agregar más.",
                    bg=COLORES["card"],
                    fg=COLORES["warning"],
                    font=("Segoe UI", 9, "italic")).pack(anchor="w", pady=(2, 5))

        tk.Label(tipos_card,
                text="Tipos de Falla y sus Colores:",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15, pady=(5, 10))

        self.tipos_list_frame = tk.Frame(tipos_card, bg=COLORES["card"])
        self.tipos_list_frame.pack(fill="x", padx=15, pady=5)

        self.cargar_lista_tipos_falla_con_colores()

        controles_tipos_frame = tk.Frame(tipos_card, bg=COLORES["card"])
        controles_tipos_frame.pack(fill="x", padx=15, pady=(10, 15))

        tk.Button(controles_tipos_frame,
                text="➕ Agregar Tipo",
                bg=COLORES["success"],
                fg=COLORES["texto"],
                font=("Segoe UI", 9),
                relief="flat",
                padx=10,
                pady=5,
                cursor="hand2",
                command=self.agregar_tipo_falla).pack(side="left", padx=5)

        # --- COLORES Y TEMAS ---
        colores_card = tk.Frame(scrollable_frame, bg=COLORES["card"], relief="flat", bd=1,
                                highlightbackground=COLORES["texto_secundario"])
        colores_card.pack(fill="x", padx=10, pady=(0, 15))

        tk.Label(colores_card,
                text="🎨 Temas y Colores",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=15, pady=(15, 10))

        # Selector de tema predefinido
        tema_frame = tk.Frame(colores_card, bg=COLORES["card"])
        tema_frame.pack(fill="x", padx=15, pady=(0, 10))

        tk.Label(tema_frame,
                text="Tema Predefinido:",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 10),
                width=20,
                anchor="w").pack(side="left")

        self.tema_selector_var = tk.StringVar(value=self.tema_actual)
        print(f"🎨 Tema actual al abrir configuración: {self.tema_actual}")
        opciones_temas = list(TEMAS_PREDEFINIDOS.keys()) + ["personalizado"]
        tema_combo = ttk.Combobox(tema_frame,
                                textvariable=self.tema_selector_var,
                                values=opciones_temas,
                                state="readonly",
                                width=15)
        tema_combo.pack(side="left", padx=5)

        # Botón para aplicar tema predefinido
        def aplicar_tema_predefinido():
            tema_elegido = self.tema_selector_var.get()
            if tema_elegido in TEMAS_PREDEFINIDOS:
                nuevos_colores = TEMAS_PREDEFINIDOS[tema_elegido]["colores"]
                
                # Actualizar la paleta actual
                self.paleta_actual = nuevos_colores.copy()
                
                # Actualizar los mapeos de compatibilidad
                self.colores["sidebar"] = nuevos_colores.get("superficie1", "#16213e")
                self.colores["card"] = nuevos_colores.get("superficie2", "#0f3460")
                self.colores["texto"] = nuevos_colores.get("texto_principal", "#ffffff")
                self.colores["texto_secundario"] = nuevos_colores.get("texto_secundario", "#b0b0b0")
                self.colores["accento"] = nuevos_colores.get("acento_principal", "#e94560")
                self.colores["exito"] = nuevos_colores.get("exito", "#00C853")
                self.colores["warning"] = nuevos_colores.get("advertencia", "#FFC107")
                self.colores["danger"] = nuevos_colores.get("peligro", "#FF5252")
                self.colores["pendiente"] = nuevos_colores.get("pendiente", "#FFA500")
                self.colores["fondo"] = nuevos_colores.get("fondo", "#1a1a2e")
                
                # Actualizar el tema actual
                self.tema_actual = tema_elegido
                
                # Actualizar los previsualizadores
                self.actualizar_previsualizacion_tema(nuevos_colores)
                
                messagebox.showinfo("Tema Aplicado", f"Tema '{TEMAS_PREDEFINIDOS[tema_elegido]['nombre']}' aplicado. Puedes personalizar los colores a continuación.")
                self.root.after(100, self.actualizar_colores_interfaz_completa)
                
        tk.Button(tema_frame,
                text="Aplicar Tema",
                bg=COLORES["accento"],
                fg=COLORES["texto"],
                font=("Segoe UI", 9),
                relief="flat",
                padx=10,
                pady=2,
                cursor="hand2",
                command=aplicar_tema_predefinido).pack(side="left", padx=5)

        tk.Label(colores_card,
                text="Personalización Avanzada:",
                bg=COLORES["card"],
                fg=COLORES["texto"],
                font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=15, pady=(10, 5))

        tk.Label(colores_card,
                text="Ajusta cada color individualmente. Los cambios en el tema predefinido se perderán.",
                bg=COLORES["card"],
                fg=COLORES["texto_secundario"],
                font=("Segoe UI", 9, "italic")).pack(anchor="w", padx=15, pady=(0, 10))

        colores_container = tk.Frame(colores_card, bg=COLORES["card"])
        colores_container.pack(fill="x", padx=15, pady=(0, 15))

        # Definimos una lista de colores con su clave, nombre mostrado y clave de compatibilidad
        colores_config = [
            ("Fondo Principal", "fondo", "color_fondo"),
            ("Superficie 1 (Sidebar)", "superficie1", "color_sidebar"),
            ("Superficie 2 (Tarjetas)", "superficie2", "color_card"),
            ("Superficie 3 (Inputs)", "superficie3", None),
            ("Texto Principal", "texto_principal", "color_texto"),
            ("Texto Secundario", "texto_secundario", "color_texto_secundario"),
            ("Acento Principal", "acento_principal", "color_acento"),
            ("Éxito", "exito", "color_exito"),
            ("Advertencia", "advertencia", "color_warning"),
            ("Peligro", "peligro", "color_danger"),
            ("Pendiente", "pendiente", "color_pendiente"),
        ]

        self.color_entries = {}  # Para guardar referencias

        for nombre_mostrar, clave_paleta, clave_sistema in colores_config:
            # Si la clave de la paleta no existe, la obtenemos de self.colores
            color_actual = self.paleta_actual.get(clave_paleta, self.colores.get(clave_paleta, "#000000"))

            frame = tk.Frame(colores_container, bg=COLORES["card"])
            frame.pack(fill="x", pady=3)

            tk.Label(frame,
                    text=nombre_mostrar + ":",
                    bg=COLORES["card"],
                    fg=COLORES["texto"],
                    font=("Segoe UI", 9),
                    width=22,
                    anchor="w").pack(side="left")

            color_frame = tk.Frame(frame, bg=color_actual, width=40, height=20)
            color_frame.pack(side="left", padx=(5, 5))
            color_frame.pack_propagate(False)

            color_label = tk.Label(color_frame,
                                text=" ",
                                bg=color_actual,
                                fg="#000000" if self.is_light_color(color_actual) else "#FFFFFF")
            color_label.pack(expand=True, fill="both")

            # Guardamos una referencia para poder actualizarla después
            self.color_entries[clave_paleta] = {
                "frame": color_frame,
                "label": color_label,
                "sistema_key": clave_sistema
            }

            def crear_comando(k):
                return lambda: self.cambiar_color_personalizado(k)

            tk.Button(frame,
                    text="Cambiar",
                    bg=COLORES["card"],
                    fg=COLORES["texto"],
                    font=("Segoe UI", 8),
                    relief="flat",
                    padx=8,
                    pady=1,
                    cursor="hand2",
                    command=crear_comando(clave_paleta)).pack(side="left", padx=(2, 0))

        # --- BOTONES DE ACCIÓN ---
        acciones_card = tk.Frame(scrollable_frame, bg=COLORES["card"], relief="flat", bd=1,
                                highlightbackground=COLORES["texto_secundario"])
        acciones_card.pack(fill="x", padx=10, pady=(0, 20))

        button_frame = tk.Frame(acciones_card, bg=COLORES["card"])
        button_frame.pack(fill="x", padx=15, pady=15)

        tk.Button(button_frame,
                text="💾 Guardar Configuración",
                bg=COLORES["success"],
                fg=COLORES["texto"],
                font=("Segoe UI", 11, "bold"),
                relief="flat",
                padx=20,
                pady=10,
                cursor="hand2",
                command=lambda: self.guardar_configuracion_actual(config_window)).pack(side="left", padx=5)

        tk.Button(button_frame,
                text="↻ Restaurar Valores por Defecto",
                bg=COLORES["warning"],
                fg=COLORES["negro"],
                font=("Segoe UI", 11),
                relief="flat",
                padx=20,
                pady=10,
                cursor="hand2",
                command=self.restaurar_valores_default).pack(side="left", padx=5)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        # Usar bind en lugar de bind_all para que solo afecte a esta ventana
        canvas.bind("<MouseWheel>", _on_mousewheel)

        def _cleanup():
            # Desvincular el evento antes de destruir
            try:
                canvas.unbind("<MouseWheel>")
            except:
                pass
            config_window.destroy()

        config_window.protocol("WM_DELETE_WINDOW", _cleanup)
        config_window.lift()
        config_window.focus_force()
    
    def cambiar_color_personalizado(self, clave_paleta):
        """Abre el selector de color para un color personalizado y actualiza la vista previa."""
        color_actual = self.paleta_actual.get(clave_paleta, self.colores.get(clave_paleta, "#000000"))
        color = colorchooser.askcolor(title=f"Seleccionar color para {clave_paleta}",
                                    initialcolor=color_actual)
        if color and color[1]:
            # Actualizar la paleta actual
            self.paleta_actual[clave_paleta] = color[1]
            
            # Actualizar los mapeos de compatibilidad
            if clave_paleta == "superficie1":
                self.colores["sidebar"] = color[1]
            elif clave_paleta == "superficie2":
                self.colores["card"] = color[1]
            elif clave_paleta == "superficie3":
                self.colores["superficie3"] = color[1]
            elif clave_paleta == "texto_principal":
                self.colores["texto"] = color[1]
            elif clave_paleta == "texto_secundario":
                self.colores["texto_secundario"] = color[1]
            elif clave_paleta == "acento_principal":
                self.colores["accento"] = color[1]
            elif clave_paleta == "advertencia":
                self.colores["warning"] = color[1]
            elif clave_paleta == "peligro":
                self.colores["danger"] = color[1]
            elif clave_paleta == "exito":
                self.colores["exito"] = color[1]
            elif clave_paleta == "pendiente":
                self.colores["pendiente"] = color[1]
            elif clave_paleta == "fondo":
                self.colores["fondo"] = color[1]
            else:
                self.colores[clave_paleta] = color[1]
            
            # Actualizar config_sistema para que se guarde
            sistema_key_map = {
                "fondo": "color_fondo",
                "superficie1": "color_sidebar",
                "superficie2": "color_card",
                "superficie3": "superficie3",
                "texto_principal": "color_texto",
                "texto_secundario": "color_texto_secundario",
                "acento_principal": "color_acento",
                "exito": "color_exito",
                "advertencia": "color_warning",
                "peligro": "color_danger",
                "pendiente": "color_pendiente"
            }
            
            if clave_paleta in sistema_key_map:
                self.config_sistema[sistema_key_map[clave_paleta]] = color[1]
            
            # Guardar configuración inmediatamente
            guardar_config_sistema(self.config_sistema, self.db_config)
            
            # Actualizar el frame de previsualización en la configuración
            if clave_paleta in self.color_entries:
                entry_data = self.color_entries[clave_paleta]
                entry_data["frame"].config(bg=color[1])
                entry_data["label"].config(bg=color[1],
                                            fg="#000000" if self.is_light_color(color[1]) else "#FFFFFF")
            
            # Actualizar inputs con los nuevos colores
            self.actualizar_colores_inputs()
            
            # Actualizar la variable del tema para indicar que es personalizado
            self.tema_selector_var.set("personalizado")
            self.tema_actual = "personalizado"
            self.config_sistema["tema_activo"] = "personalizado"

    def actualizar_previsualizacion_tema(self, nuevos_colores):
        """Actualiza todos los selectores de color de la UI de configuración con los colores de un tema."""
        for clave_paleta, color_hex in nuevos_colores.items():
            if clave_paleta in self.color_entries:
                entry_data = self.color_entries[clave_paleta]
                entry_data["frame"].config(bg=color_hex)
                entry_data["label"].config(bg=color_hex,
                                            fg="#000000" if self.is_light_color(color_hex) else "#FFFFFF")
                # Actualizar también la paleta actual en memoria
                self.paleta_actual[clave_paleta] = color_hex
                
                # Actualizar los mapeos de compatibilidad
                if clave_paleta == "superficie1":
                    self.colores["sidebar"] = color_hex
                elif clave_paleta == "superficie2":
                    self.colores["card"] = color_hex
                elif clave_paleta == "texto_principal":
                    self.colores["texto"] = color_hex
                elif clave_paleta == "texto_secundario":
                    self.colores["texto_secundario"] = color_hex
                elif clave_paleta == "acento_principal":
                    self.colores["accento"] = color_hex
                elif clave_paleta == "advertencia":
                    self.colores["warning"] = color_hex
                elif clave_paleta == "peligro":
                    self.colores["danger"] = color_hex
                elif clave_paleta == "exito":
                    self.colores["exito"] = color_hex
                elif clave_paleta == "pendiente":
                    self.colores["pendiente"] = color_hex
                elif clave_paleta == "fondo":
                    self.colores["fondo"] = color_hex
                elif clave_paleta == "superficie3":
                    self.colores["superficie3"] = color_hex
        
        # Actualizar inputs con los nuevos colores
        self.actualizar_colores_inputs()

    def probar_conexion_bd(self):
        try:
            config = {
                "tipo": "mysql",
                "host": self.db_host_var.get(),
                "port": int(self.db_port_var.get()),
                "usuario": self.db_user_var.get(),
                "password": self.db_pass_var.get(),
                "base_datos": self.db_name_var.get(),
                "timeout": int(self.db_timeout_var.get()),
                "usar_ssl": self.db_ssl_var.get()
            }

            if config["tipo"] == "mysql":
                exito, mensaje = probar_conexion_mysql(config)
                if exito:
                    self.db_estado_label.config(
                        text="✅ Conexión exitosa a MySQL",
                        fg=COLORES["success"]
                    )
                    messagebox.showinfo("Éxito", "Conexión a MySQL establecida correctamente.")
                else:
                    self.db_estado_label.config(
                        text=f"❌ Error: {mensaje}",
                        fg=COLORES["danger"]
                    )
                    messagebox.showerror("Error de Conexión", f"No se pudo conectar a MySQL:\n{mensaje}")

        except Exception as e:
            self.db_estado_label.config(
                text=f"❌ Error: {str(e)}",
                fg=COLORES["danger"]
            )
            messagebox.showerror("Error", f"Error al probar conexión:\n{str(e)}")

    def inicializar_bd_desde_config(self):
        try:
            config = {
                "tipo": self.db_tipo_var.get(),
                "host": self.db_host_var.get(),
                "port": int(self.db_port_var.get()),
                "usuario": self.db_user_var.get(),
                "password": self.db_pass_var.get(),
                "base_datos": self.db_name_var.get(),
                "timeout": int(self.db_timeout_var.get()),
                "usar_ssl": self.db_ssl_var.get()
            }

            if config["tipo"] == "mysql":
                exito, mensaje = inicializar_db_mysql(config)
                if exito:
                    self.db_estado_label.config(
                        text="✅ Base de datos inicializada",
                        fg=COLORES["success"]
                    )
                    messagebox.showinfo("Éxito", "Base de datos MySQL inicializada correctamente.")
                else:
                    self.db_estado_label.config(
                        text=f"❌ Error: {mensaje}",
                        fg=COLORES["danger"]
                    )
                    messagebox.showerror("Error", f"No se pudo inicializar la base de datos:\n{mensaje}")
        

        except Exception as e:
            messagebox.showerror("Error", f"Error al inicializar base de datos:\n{str(e)}")

    def cargar_lista_tipos_falla_con_colores(self):
        for widget in self.tipos_list_frame.winfo_children():
            widget.destroy()

        info_frame = tk.Frame(self.tipos_list_frame, bg=COLORES["card"])
        info_frame.pack(fill="x", pady=(0, 5))

        if len(self.tipos_falla) >= self.max_tipos_falla:
            color_limite = COLORES["danger"]
            mensaje = f"⚠️ LÍMITE ALCANZADO: {len(self.tipos_falla)}/{self.max_tipos_falla}"
        elif len(self.tipos_falla) >= self.max_tipos_falla - 1:
            color_limite = COLORES["warning"]
            mensaje = f"⚠️ Casi al límite: {len(self.tipos_falla)}/{self.max_tipos_falla}"
        else:
            color_limite = COLORES["success"]
            mensaje = f"✅ Tipos disponibles: {len(self.tipos_falla)}/{self.max_tipos_falla}"

        tk.Label(info_frame,
                text=mensaje,
                bg=COLORES["card"],
                fg=color_limite,
                font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=5)

        colores_base = ["mantenimiento", "produccion", "calidad", "materiales", "ingenieria",
                        "success", "warning", "danger", "accento"]

        for i, tipo in enumerate(self.tipos_falla):
            frame = tk.Frame(self.tipos_list_frame, bg=COLORES["card"])
            frame.pack(fill="x", pady=2)

            tk.Label(frame,
                    text=f"{i+1}. ",
                    bg=COLORES["card"],
                    fg=COLORES["texto_secundario"],
                    font=("Segoe UI", 9)).pack(side="left", padx=(5, 0))

            entry_var = tk.StringVar(value=tipo)
            entry = tk.Entry(frame,
                        textvariable=entry_var,
                        bg=COLORES.get("superficie3", "#2d3047"),  # ← USA EL COLOR DEL TEMA
                        fg=COLORES["texto"],
                        relief="flat",
                        font=("Segoe UI", 9),
                        width=15)
            entry.pack(side="left", padx=(0, 5))
            entry.var = entry_var
            entry.index = i

            color_key = None
            for key in colores_base:
                if key in COLORES and f"{key}_tipo" == tipo.lower().replace(" ", "_"):
                    color_key = key
                    break

            if not color_key and i < len(colores_base):
                color_key = colores_base[i]
            elif not color_key:
                color_key = "accento"

            tipo_color_key = f"{tipo.lower().replace(' ', '_')}_color"
            if tipo_color_key not in COLORES:
                COLORES[tipo_color_key] = COLORES[color_key]

            color_frame = tk.Frame(frame, bg=COLORES[tipo_color_key], width=50, height=20)
            color_frame.pack(side="left", padx=(5, 5))
            color_frame.pack_propagate(False)

            color_label = tk.Label(color_frame,
                                text="Color",
                                bg=COLORES[tipo_color_key],
                                fg="#000000" if self.is_light_color(COLORES[tipo_color_key]) else "#FFFFFF",
                                font=("Segoe UI", 8))
            color_label.pack(expand=True, fill="both")

            tk.Button(frame,
                    text="🎨",
                    bg=COLORES["card"],
                    fg=COLORES["texto"],
                    font=("Segoe UI", 8),
                    relief="flat",
                    width=2,
                    cursor="hand2",
                    command=lambda t=tipo, l=color_label, idx=i: self.cambiar_color_tipo_falla(t, l, idx)).pack(side="left", padx=(0, 5))

            tk.Button(frame,
                    text="✕",
                    bg=COLORES["danger"],
                    fg=COLORES["texto"],
                    font=("Segoe UI", 8),
                    relief="flat",
                    width=2,
                    cursor="hand2",
                    command=lambda idx=i: self.eliminar_tipo_falla(idx)).pack(side="left", padx=(0, 5))

            entry.var = entry_var
            entry.index = i
            entry.color_label = color_label

    def cambiar_color_tipo_falla(self, tipo, label, index):
        color_key = f"{tipo.lower().replace(' ', '_')}_color"
        color = colorchooser.askcolor(title=f"Seleccionar color para {tipo}",
                                    initialcolor=COLORES.get(color_key, COLORES["accento"]))
        if color[1]:
            COLORES[color_key] = color[1]
            label.config(text="Color", bg=color[1],
                        fg="#000000" if self.is_light_color(color[1]) else "#FFFFFF")
            
            # ✅ Actualizar el color en tipos_falla_data
            for t in self.tipos_falla_data:
                if t["nombre"] == tipo:
                    t["color"] = color[1]
                    break
            
            # ✅ Guardar usando la función NUEVA
            guardar_tipos_falla(self.tipos_falla_data, self.db_config)
            
            self.actualizar_tabla()

    def is_light_color(self, color):
        if color.startswith('#'):
            color = color.lstrip('#')
            rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        else:
            rgb = color
        luminosidad = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255
        return luminosidad > 0.5

    def agregar_tipo_falla(self):
        print(f"🔍 DEBUG - Intentando agregar tipo de falla")
        print(f"   Tipos actuales: {len(self.tipos_falla)}")
        print(f"   Límite (max_tipos_falla): {self.max_tipos_falla}")
        print(f"   Tipo de licencia: {self.licencia_config.get('license_type')}")

        if len(self.tipos_falla) >= self.max_tipos_falla:
            print(f"❌ DEBUG - Límite alcanzado, no se puede agregar más")
            messagebox.showwarning(
                "Límite Alcanzado",
                f"Has alcanzado el límite de {self.max_tipos_falla} tipos de falla\n"
                f"permitidos para tu licencia actual ({self.licencia_config.get('license_type', 'basic').upper()}).\n\n"
                "Elimina algún tipo existente o actualiza tu licencia para agregar más.",
                parent=self.config_window if hasattr(self, 'config_window') and self.config_window and self.config_window.winfo_exists() else self.root
            )
            return

        dialog = tk.Toplevel(self.config_window if hasattr(self, 'config_window') else self.root)
        dialog.title("Nuevo Tipo de Falla")
        dialog.geometry("400x200")
        dialog.configure(bg=COLORES["fondo"])
        dialog.transient(self.config_window if hasattr(self, 'config_window') else self.root)
        dialog.grab_set()

        dialog.update_idletasks()
        x = dialog.master.winfo_x() + (dialog.master.winfo_width() // 2) - (400 // 2)
        y = dialog.master.winfo_y() + (dialog.master.winfo_height() // 2) - (200 // 2)
        dialog.geometry(f"+{x}+{y}")

        tk.Label(dialog,
                text="➕ Agregar Nuevo Tipo de Falla",
                bg=COLORES["fondo"],
                fg=COLORES["texto"],
                font=("Segoe UI", 14, "bold")).pack(pady=20)

        tk.Label(dialog,
                text="Nombre del nuevo tipo:",
                bg=COLORES["fondo"],
                fg=COLORES["texto_secundario"],
                font=("Segoe UI", 10)).pack(pady=(0, 5))

        entry = ModernEntry(dialog, width=30)
        entry.pack(pady=10)
        entry.focus()

        def confirmar():
            nuevo_tipo = entry.get().strip()
            if nuevo_tipo:
                if nuevo_tipo in self.tipos_falla:
                    messagebox.showwarning("Aviso", "Este tipo de falla ya existe.", parent=dialog)
                    return

                if len(self.tipos_falla) >= self.max_tipos_falla:
                    messagebox.showwarning(
                        "Límite Alcanzado",
                        f"Has alcanzado el límite de {self.max_tipos_falla} tipos de falla.",
                        parent=dialog
                    )
                    dialog.destroy()
                    return

                self.tipos_falla.append(nuevo_tipo)

                import random
                color = f"#{random.randint(0, 255):02x}{random.randint(0, 255):02x}{random.randint(0, 255):02x}"
                color_key = f"{nuevo_tipo.lower().replace(' ', '_')}_color"
                COLORES[color_key] = color
                COLORES["fallas"] = self.tipos_falla

                # ✅ CORREGIDO: Actualizar self.tipos_falla_data
                self.tipos_falla_data.append({"nombre": nuevo_tipo, "color": color})

                # ✅ Guardar usando las funciones NUEVAS
                guardar_tipos_falla(self.tipos_falla_data, self.db_config)

                self.cargar_lista_tipos_falla_con_colores()
                self.actualizar_comboboxes_tipos()

                messagebox.showinfo("✅ Éxito", f"Tipo '{nuevo_tipo}' agregado correctamente.", parent=dialog)
                dialog.destroy()
            else:
                messagebox.showwarning("Aviso", "Por favor ingresa un nombre válido.", parent=dialog)

        tk.Button(dialog,
                text="✅ Agregar",
                bg=COLORES["success"],
                fg=COLORES["texto"],
                font=("Segoe UI", 11, "bold"),
                relief="flat",
                padx=20,
                pady=8,
                cursor="hand2",
                command=confirmar).pack(pady=20)

        dialog.bind('<Return>', lambda e: confirmar())
    
    def eliminar_tipo_falla(self, index):
        tipo_a_eliminar = self.tipos_falla[index]

        if hasattr(self, 'config_window') and self.config_window.winfo_exists():
            self.config_window.lift()
            self.config_window.focus_force()

        respuesta = messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Eliminar el tipo '{tipo_a_eliminar}'?\n\n"
            "⚠️ ADVERTENCIA: Esta acción eliminará permanentemente:\n"
            f"• El tipo de falla '{tipo_a_eliminar}'\n"
            "• Su color asociado\n"
            "• Todos los registros de este tipo en el historial\n\n"
            "¿Estás seguro?",
            parent=self.config_window
        )

        if respuesta:
            try:
                conn = self._conectar_mysql()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM fallas WHERE tipo = %s", (tipo_a_eliminar,))
                    registros_eliminados = cursor.rowcount
                    conn.commit()
                    conn.close()

                print(f"✅ Eliminados {registros_eliminados} registros de '{tipo_a_eliminar}' de la BD")

                # Eliminar de las listas
                del self.tipos_falla[index]
                # ✅ También eliminar de tipos_falla_data
                if index < len(self.tipos_falla_data):
                    del self.tipos_falla_data[index]

                color_key = f"{tipo_a_eliminar.lower().replace(' ', '_')}_color"
                if color_key in COLORES:
                    del COLORES[color_key]

                self.fallas_activas = [a for a in self.fallas_activas if a["tipo"] != tipo_a_eliminar]

                COLORES["fallas"] = self.tipos_falla

                # ✅ Guardar usando las funciones NUEVAS
                guardar_tipos_falla(self.tipos_falla_data, self.db_config)

                self.cargar_lista_tipos_falla_con_colores()
                self.actualizar_comboboxes_tipos()
                self.actualizar_tabla()
                self.update_stats()

                messagebox.showinfo(
                    "✅ Eliminación Exitosa",
                    f"Tipo '{tipo_a_eliminar}' eliminado permanentemente.\n"
                    f"Se eliminaron {registros_eliminados} registros del historial.\n\n"
                    "Los cambios se guardaron automáticamente.",
                    parent=self.config_window
                )

            except Exception as e:
                messagebox.showerror(
                    "❌ Error",
                    f"No se pudo eliminar el tipo de falla:\n{str(e)}",
                    parent=self.config_window
                )
    
    def actualizar_comboboxes_tipos(self):
        if hasattr(self, 'filtro_tipo'):
            self.filtro_tipo['values'] = [""] + self.tipos_falla
        self.actualizar_botones_tipos()
        COLORES["fallas"] = self.tipos_falla

    def cambiar_nombre_sistema(self):
        nuevo_nombre = self.entry_nombre.get().strip()
        if nuevo_nombre:
            self.nombre_sistema = nuevo_nombre
            self.colores["nombre_sistema"] = nuevo_nombre
            self.config_sistema["nombre_sistema"] = nuevo_nombre
            self.logo_label.config(text=f"⚙️ {nuevo_nombre}")
            
            # ✅ Guardar usando la función NUEVA
            guardar_config_sistema(self.config_sistema, self.db_config)
            
            messagebox.showinfo("Éxito", f"Nombre cambiado a: {nuevo_nombre}")

    def cambiar_color(self, color_key, label):
        color = colorchooser.askcolor(title=f"Seleccionar color para {color_key}",
                                    initialcolor=COLORES[color_key])
        if color[1]:
            COLORES[color_key] = color[1]
            self.colores[color_key] = color[1]
            
            # Actualizar config_sistema si es un color del sistema
            sistema_key_map = {
                "fondo": "color_fondo",
                "sidebar": "color_sidebar",
                "card": "color_card",
                "texto": "color_texto",
                "texto_secundario": "color_texto_secundario",
                "accento": "color_acento",
                "exito": "color_exito",
                "warning": "color_warning",
                "danger": "color_danger",
                "pendiente": "color_pendiente"
            }
            if color_key in sistema_key_map:
                self.config_sistema[sistema_key_map[color_key]] = color[1]
            
            label.config(text=color[1], bg=color[1],
                        fg="#000000" if self.is_light_color(color[1]) else "#FFFFFF")
            
            # ✅ Guardar usando la función NUEVA
            guardar_config_sistema(self.config_sistema, self.db_config)
            
            if color_key in ["fondo", "sidebar", "card", "texto", "accento"]:
                self.actualizar_colores_interface()
                self.actualizar_colores_configuracion()

    def actualizar_colores_configuracion(self):
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Toplevel) and widget.title() == "Configuración del Sistema":
                widget.configure(bg=COLORES["fondo"])
                def actualizar_widgets_config(w):
                    try:
                        if isinstance(w, tk.Frame) or isinstance(w, tk.LabelFrame):
                            if w != self.tipos_list_frame:
                                try:
                                    if w.cget('bg') not in [COLORES["card"], "#2d3047", COLORES["danger"], COLORES["success"], COLORES["warning"]]:
                                        w.config(bg=COLORES["fondo"])
                                except:
                                    pass
                        if isinstance(w, tk.Label):
                            try:
                                if w.cget('bg') not in [COLORES["danger"], COLORES["success"], COLORES["warning"], COLORES["accento"]]:
                                    if w.cget('bg') == COLORES["fondo"] or w.cget('bg') == COLORES["card"]:
                                        w.config(bg=COLORES["fondo"], fg=COLORES["texto"])
                                    elif w.cget('bg') == COLORES["card"]:
                                        w.config(bg=COLORES["card"], fg=COLORES["texto"])
                            except:
                                pass
                        if isinstance(w, tk.Entry):
                            try:
                                if w.cget('bg') == "#2d3047":
                                    w.config(fg=COLORES["texto"])
                            except:
                                pass
                        for child in w.winfo_children():
                            actualizar_widgets_config(child)
                    except:
                        pass
                actualizar_widgets_config(widget)
                break

    def actualizar_colores_interface(self):
        self.sidebar.config(bg=COLORES["fondo"])
        self.logo_label.config(bg=COLORES["sidebar"], fg=COLORES["texto"])
        for widget in self.sidebar.winfo_children():
            if isinstance(widget, tk.Button):
                widget.config(bg=COLORES["sidebar"], fg=COLORES["texto_secundario"])
        self.main_content.config(bg=COLORES["fondo"])
        self.header_frame.config(bg=COLORES["card"])
        self.header_label.config(bg=COLORES["card"], fg=COLORES["texto"])
        self.status_frame.config(bg=COLORES["card"])
        self.status_label.config(bg=COLORES["card"], fg=COLORES["texto_secundario"])
        if hasattr(self, 'frame_principal'):
            self.frame_principal.config(bg=COLORES["fondo"])
        if hasattr(self, 'frame_historial'):
            self.frame_historial.config(bg=COLORES["fondo"])

    def get_color_for_tipo(self, tipo):
        """
        Obtiene el color asociado a un tipo de falla.
        La fuente de verdad es el diccionario COLORES con la clave 'nombre_color'.
        """
        # 1. Construir la clave estandarizada para buscar en COLORES
        tipo_color_key = f"{tipo.lower().replace(' ', '_')}_color"

        # 2. Buscar en COLORES (que ya tiene los datos de config_tipos_falla)
        if tipo_color_key in COLORES and COLORES[tipo_color_key]:
            return COLORES[tipo_color_key]

        # 3. Fallback 1: Mapa de colores por defecto para nombres conocidos
        colores_base_mapa = {
            "mantenimiento": COLORES.get("mantenimiento", "#FF9A00"),
            "producción": COLORES.get("produccion", "#FF5252"),
            "produccion": COLORES.get("produccion", "#FF5252"),
            "calidad": COLORES.get("calidad", "#4CAF50"),
            "materiales": COLORES.get("materiales", "#2196F3"),
            "ingeniería": COLORES.get("ingenieria", "#9C27B0"),
            "ingenieria": COLORES.get("ingenieria", "#9C27B0")
        }
        tipo_lower = tipo.lower()
        for key, color in colores_base_mapa.items():
            if tipo_lower == key:
                return color

        # 4. Fallback 2: Generar un color basado en hash (último recurso)
        import hashlib
        hash_obj = hashlib.md5(tipo.encode())
        hash_int = int(hash_obj.hexdigest(), 16)
        hue = (hash_int % 360) / 360.0
        saturation = 0.7
        value = 0.6
        from colorsys import hsv_to_rgb
        r, g, b = hsv_to_rgb(hue, saturation, value)
        return f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'

    def guardar_configuracion_actual(self, window):
        """Guarda la configuración actual del sistema"""
        try:
            # Guardar configuración de BD
            self.db_config["tipo"] = self.db_tipo_var.get()
            self.db_config["host"] = self.db_host_var.get()
            self.db_config["port"] = int(self.db_port_var.get())
            self.db_config["usuario"] = self.db_user_var.get()
            self.db_config["password"] = self.db_pass_var.get()
            self.db_config["base_datos"] = self.db_name_var.get()
            self.db_config["timeout"] = int(self.db_timeout_var.get())
            self.db_config["usar_ssl"] = self.db_ssl_var.get()

            guardar_config_db(self.db_config)  # ✅ ESTO SÍ SE QUEDA (guarda db_config.json)

            if self.db_config["tipo"] == "mysql":
                exito, mensaje = probar_conexion_mysql(self.db_config)
                self.db_estado = exito
                if exito:
                    print(f"✅ MySQL configurado correctamente: {mensaje}")
                    #inicializar_db_mysql(self.db_config)
                else:
                    print(f"⚠️ Problema con MySQL: {mensaje}")


            # Guardar nombre del sistema
            if hasattr(self, 'entry_nombre') and self.entry_nombre.winfo_exists():
                nuevo_nombre = self.entry_nombre.get().strip()
                if nuevo_nombre:
                    self.nombre_sistema = nuevo_nombre
                    self.colores["nombre_sistema"] = nuevo_nombre
                    self.logo_label.config(text=f"⚙️ {nuevo_nombre}")

            # Procesar tipos de falla
            nuevos_tipos = []
            nuevos_tipos_data = []  # ✅ NUEVO: guardar también los colores
            if hasattr(self, 'tipos_list_frame') and self.tipos_list_frame.winfo_exists():
                for widget in self.tipos_list_frame.winfo_children():
                    if isinstance(widget, tk.Frame):
                        tipo_entry = None
                        color_label = None
                        
                        for child in widget.winfo_children():
                            if isinstance(child, tk.Entry):
                                if hasattr(child, 'var'):
                                    tipo = child.var.get().strip()
                                    if tipo:
                                        nuevos_tipos.append(tipo)
                                        tipo_entry = tipo
                            
                            if isinstance(child, tk.Frame):
                                for subchild in child.winfo_children():
                                    if isinstance(subchild, tk.Label) and subchild.cget('text') == "Color":
                                        color_label = subchild

                        if tipo_entry and color_label and color_label.winfo_exists():
                            color = color_label.cget("bg")
                            nuevos_tipos_data.append({"nombre": tipo_entry, "color": color})
                            
            if hasattr(self, 'mapeo_vars'):
                nuevo_mapeo = {}
                for numero_boton, var in self.mapeo_vars.items():
                    tipo_seleccionado = var.get().strip()
                    if tipo_seleccionado:  # Solo guardar si seleccionó algo
                        nuevo_mapeo[numero_boton] = tipo_seleccionado
                
                if nuevo_mapeo:
                    guardar_mapeo_botones(nuevo_mapeo, self.db_config)
                    # Actualizar el diccionario en memoria
                    self.mapeo_botones = nuevo_mapeo
                    print(f"✅ Mapeo de botones guardado: {nuevo_mapeo}")
                else:
                    # Si no hay mapeo, guardar vacío (borrar todo)
                    guardar_mapeo_botones({}, self.db_config)
                    self.mapeo_botones = {}
                    print("✅ Mapeo de botones borrado")

            # Verificar límite de licencia
            if len(nuevos_tipos) > self.max_tipos_falla:
                messagebox.showwarning(
                    "Límite de Tipos Excedido",
                    f"Estás intentando guardar {len(nuevos_tipos)} tipos de falla, pero\n"
                    f"tu licencia actual ({self.licencia_config.get('license_type', 'basic').upper()}) "
                    f"solo permite {self.max_tipos_falla}.\n\n"
                    "Se recortará la lista automáticamente.",
                    parent=window
                )
                nuevos_tipos = nuevos_tipos[:self.max_tipos_falla]
                nuevos_tipos_data = nuevos_tipos_data[:self.max_tipos_falla]

            if nuevos_tipos:
                self.tipos_falla = nuevos_tipos
                self.tipos_falla_data = nuevos_tipos_data
                self.colores["fallas"] = nuevos_tipos
                self.actualizar_comboboxes_tipos()
                
                # ✅ Guardar tipos de falla (solo aquí, cuando se guarda configuración)
                guardar_tipos_falla(self.tipos_falla_data, self.db_config)
            else:
                messagebox.showerror(
                    "Error",
                    "Debe existir al menos un tipo de falla.",
                    parent=window
                )
                return

            # Actualizar config_sistema con los colores actuales
            self.config_sistema["nombre_sistema"] = self.nombre_sistema

            # Guardar el tema activo
            self.config_sistema["tema_activo"] = self.tema_actual

            # Guardar TODOS los colores
            mapeo_colores = {
                "color_fondo": "fondo",
                "color_sidebar": "sidebar",
                "color_card": "card",
                "superficie3": "superficie3",
                "color_texto": "texto",
                "texto_principal": "texto_principal",
                "color_texto_secundario": "texto_secundario",
                "texto_secundario": "texto_secundario",
                "color_acento": "accento",
                "acento_principal": "acento_principal",
                "color_exito": "exito",
                "exito": "exito",
                "color_warning": "warning",
                "advertencia": "advertencia",
                "color_danger": "danger",
                "peligro": "peligro",
                "color_pendiente": "pendiente",
                "pendiente": "pendiente"
            }

            for columna_bd, clave_color in mapeo_colores.items():
                if clave_color in self.colores:
                    self.config_sistema[columna_bd] = self.colores[clave_color]

            # Guardar configuración del sistema
            guardar_config_sistema(self.config_sistema, self.db_config)
            self.tema_actual = self.config_sistema.get("tema_activo", "oscuro")

            # Actualizar interfaz
            self.actualizar_tabla()
            self.update_stats()

            messagebox.showinfo("✅ Éxito",
                            "Configuración guardada exitosamente.\n"
                            "Los cambios se aplicarán inmediatamente.",
                            parent=window)
            
            # Cerrar la ventana de configuración
            try:
                window.destroy()
            except:
                pass

        except Exception as e:
            print(f"❌ Error en guardar_configuracion_actual: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("❌ Error",
                            f"No se pudo guardar la configuración:\n{str(e)}",
                            parent=window if window.winfo_exists() else self.root)
        
    def diagnosticar_base_datos(self):
        """Diagnóstico de la base de datos MySQL"""
        print(f"\n=== DIAGNÓSTICO DE BASE DE DATOS MYSQL ===")
        print(f"Configuración: {self.db_config['host']}/{self.db_config['base_datos']}")
        
        conn = self._conectar_mysql(timeout=5)
        if not conn:
            print("❌ No se pudo conectar a MySQL")
            messagebox.showerror("Error", "No se pudo conectar a MySQL")
            return
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM fallas")
            total_historial = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM fallas_activas")
            total_activas = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            print(f"✅ Conexión exitosa")
            print(f"📊 Fallas en historial: {total_historial}")
            print(f"📊 Fallas activas: {total_activas}")
            
            messagebox.showinfo("Diagnóstico BD",
                            f"Conexión MySQL exitosa\n"
                            f"Host: {self.db_config['host']}\n"
                            f"Base de datos: {self.db_config['base_datos']}\n\n"
                            f"Fallas en historial: {total_historial}\n"
                            f"Fallas activas: {total_activas}")
        except Exception as e:
            print(f"❌ Error en diagnóstico: {e}")
            messagebox.showerror("Error", f"Error en diagnóstico:\n{str(e)}")
        
    def restaurar_valores_default(self):
        respuesta = messagebox.askyesno("Confirmar",
                                    "¿Estás seguro de restaurar los valores por defecto?\n" +
                                    "Se perderán todos los cambios personalizados, incluyendo tipos de falla.")
        if respuesta:
            # Restaurar colores por defecto
            COLORES = COLORES_DEFAULT.copy()
            self.colores = COLORES_DEFAULT.copy()
            
            # Restaurar tipos de falla por defecto
            self.tipos_falla = FALLAS_DEFAULT.copy()
            self.tipos_falla_data = [
                {"nombre": "Mantenimiento", "color": "#FF9A00"},
                {"nombre": "Producción", "color": "#FF5252"},
                {"nombre": "Calidad", "color": "#4CAF50"},
                {"nombre": "Materiales", "color": "#2196F3"},
                {"nombre": "Ingeniería", "color": "#9C27B0"}
            ]

            if len(self.tipos_falla) > self.max_tipos_falla:
                self.tipos_falla = self.tipos_falla[:self.max_tipos_falla]
                self.tipos_falla_data = self.tipos_falla_data[:self.max_tipos_falla]
                COLORES["fallas"] = self.tipos_falla
                messagebox.showinfo(
                    "Límite Aplicado",
                    f"La lista de tipos de falla se ha recortado a {self.max_tipos_falla} "
                    f"para cumplir con tu licencia actual."
                )

            # Actualizar config_sistema
            sistema_key_map = {
                "color_fondo": "fondo",
                "color_sidebar": "sidebar",
                "color_card": "card",
                "color_texto": "texto",
                "color_texto_secundario": "texto_secundario",
                "color_acento": "accento",
                "color_exito": "exito",
                "color_warning": "warning",
                "color_danger": "danger",
                "color_pendiente": "pendiente"
            }
            for sistema_key, color_key in sistema_key_map.items():
                if color_key in self.colores:
                    self.config_sistema[sistema_key] = self.colores[color_key]
            
            self.config_sistema["nombre_sistema"] = "ANDON SYSTEM"
            self.nombre_sistema = "ANDON SYSTEM"

            # Guardar usando funciones NUEVAS
            guardar_config_sistema(self.config_sistema, self.db_config)
            guardar_tipos_falla(self.tipos_falla_data, self.db_config)

            # Actualizar interfaz
            self.actualizar_colores_interface()
            self.actualizar_comboboxes_tipos()
            if hasattr(self, 'entry_nombre'):
                self.entry_nombre.delete(0, tk.END)
                self.entry_nombre.insert(0, "ANDON SYSTEM")
            if hasattr(self, 'tipos_list_frame'):
                self.cargar_lista_tipos_falla_con_colores()

            self.logo_label.config(text=f"⚙️ {self.nombre_sistema}")

            messagebox.showinfo("Éxito", "Valores por defecto restaurados.\n" +
                                "Los cambios se han guardado.")
        
    def generar_reporte_pdf(self):
        messagebox.showinfo("Información",
                          "Función de generación de reporte PDF en desarrollo.\n"
                          "Por ahora usa la función 'Exportar Excel' para obtener reportes detallados.")
        
    #====================metodos actuaillizacion automatica de pantalla======================================
    def iniciar_actualizacion_automatica(self):
        """Inicia el temporizador para actualización automática cada 60 segundos"""
        
        # Asegurar que la variable existe
        self.timer_auto_actualizacion = None
        
        def actualizar_periodicamente():
            try:
                print(f"🔄 Actualización automática a las {datetime.now().strftime('%H:%M:%S')}")
                
                # Guardar estado actual para comparar después
                fallas_anteriores = self.fallas_activas.copy()
                
                # Recargar fallas activas desde la BD
                nuevas_fallas = cargar_fallas_activas(self.db_config)
                
                # Verificar si hubo cambios
                if self.hubo_cambios_en_fallas(self.fallas_activas, nuevas_fallas):
                    print(f"📊 Cambios detectados! Actualizando interfaz...")
                    self.fallas_activas = nuevas_fallas
                    
                    # ACTUALIZAR PANTALLA PRINCIPAL
                    self.root.after(0, self.actualizar_tabla)
                    self.root.after(0, self.update_stats)
                    
                    # Verificar si el contador principal necesita actualización
                    if hasattr(self, 'contador_fallas'):
                        self.root.after(0, lambda: self.contador_fallas.config(
                            text=f"{len(self.fallas_activas)} activas"))
                    
                    # ACTUALIZAR PROYECCIÓN si está abierta
                    if self.ventana_proyeccion and self.ventana_proyeccion.winfo_exists():
                        self.root.after(0, self.actualizar_tabla_proyeccion)
                        if hasattr(self, 'proj_counter') and self.proj_counter and self.proj_counter.winfo_exists():
                            self.root.after(0, lambda: self.proj_counter.config(
                                text=str(len(self.fallas_activas))))
                else:
                    print("📊 Sin cambios en las fallas activas")
                    # Aún así, actualizar por si acaso (opcional, puedes comentar estas líneas)
                    self.fallas_activas = nuevas_fallas
                    self.root.after(0, self.actualizar_tabla)
                    self.root.after(0, self.update_stats)
                
                # Actualizar hora de la proyección (siempre, aunque no haya cambios)
                if self.ventana_proyeccion and self.ventana_proyeccion.winfo_exists():
                    self.root.after(0, self.actualizar_hora_proyeccion)
                
            except Exception as e:
                print(f"❌ Error en actualización automática: {e}")
                import traceback
                traceback.print_exc()
            
            # Programar la siguiente actualización (60 segundos)
            if hasattr(self, 'root') and self.root:
                self.timer_auto_actualizacion = self.root.after(60000, actualizar_periodicamente)
        
        # Iniciar el ciclo
        if hasattr(self, 'root') and self.root:
            self.timer_auto_actualizacion = self.root.after(60000, actualizar_periodicamente)
            print("✅ Actualización automática iniciada (cada 60 segundos) - Pantalla principal y proyección")
              
    def hubo_cambios_en_fallas(self, fallas_viejas, fallas_nuevas):
        """Compara dos listas de fallas para detectar cambios"""
        if len(fallas_viejas) != len(fallas_nuevas):
            return True
        
        # Crear diccionarios para comparación más rápida
        dict_viejo = {}
        for f in fallas_viejas:
            key = (f.get('maquina'), f.get('tipo'), f.get('numero_falla', 0))
            dict_viejo[key] = f
        
        dict_nuevo = {}
        for f in fallas_nuevas:
            key = (f.get('maquina'), f.get('tipo'), f.get('numero_falla', 0))
            dict_nuevo[key] = f
        
        # Comparar
        for key, falla_vieja in dict_viejo.items():
            if key not in dict_nuevo:
                return True  # Falla eliminada
            
            falla_nueva = dict_nuevo[key]
            
            # Comparar campos importantes
            campos_a_comparar = ['estado', 'proceso', 'fin', 'nota_pendiente']
            for campo in campos_a_comparar:
                if falla_vieja.get(campo) != falla_nueva.get(campo):
                    return True  # Cambio detectado
        
        return False
    
    def iniciar_monitoreo(self):
        """Inicia hilo de monitoreo de rendimiento"""
        
        def monitorear():
            while True:
                try:
                    # CPU
                    cpu = psutil.cpu_percent(interval=1)
                    
                    # Memoria
                    memoria = psutil.virtual_memory().percent
                    
                    # Tamaño de la cola de eventos (si existe)
                    cola_tamano = self.event_queue.qsize() if hasattr(self, 'event_queue') else 0
                    
                    # Número de fallas activas
                    fallas_activas = len(self.fallas_activas)
                    
                    # Número de hilos activos
                    hilos_activos = threading.active_count()
                    
                    # Alertas si algo está mal
                    if cola_tamano > 1000:
                        print(f"⚠️ ALERTA: Cola de eventos muy grande: {cola_tamano}")
                    
                    if cpu > 80:
                        print(f"⚠️ ALERTA: CPU alto: {cpu}%")
                    
                    if memoria > 85:
                        print(f"⚠️ ALERTA: Memoria alta: {memoria}%")
                    
                    # Log cada 60 segundos
                    print(f"📊 MONITOREO: CPU={cpu}%, RAM={memoria}%, "
                        f"Cola={cola_tamano}, Fallas={fallas_activas}, Hilos={hilos_activos}")
                    
                    time.sleep(60)  # Esperar 60 segundos
                    
                except Exception as e:
                    print(f"❌ Error en monitoreo: {e}")
                    time.sleep(60)  # Seguir intentando
        
        # Iniciar el hilo de monitoreo (daemon=True para que se cierre con la app)
        hilo_monitoreo = threading.Thread(target=monitorear, daemon=True)
        hilo_monitoreo.start()
        print("✅ Monitoreo de rendimiento iniciado")
        
    def actualizar_colores_interfaz_completa(self):
        """Actualiza todos los colores de la interfaz después de un cambio de tema"""
        
        # Actualizar estilos de ttk
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview",
                        background=COLORES["card"],
                        foreground=COLORES["texto"],
                        rowheight=35,
                        fieldbackground=COLORES["card"],
                        borderwidth=0,
                        font=("Segoe UI", 10))
        style.configure("Treeview.Heading",
                        background=COLORES["sidebar"],
                        foreground=COLORES["texto"],
                        relief="flat",
                        borderwidth=0,
                        font=("Segoe UI", 11, "bold"))
        style.map('Treeview',
                background=[('selected', COLORES["accento"])],
                foreground=[('selected', COLORES["texto"])])
        
        # Actualizar combobox style
        style.configure("TCombobox",
                        fieldbackground=COLORES.get("superficie3", "#2d3047"),
                        background=COLORES.get("superficie3", "#2d3047"),
                        foreground=COLORES["texto"],
                        borderwidth=0,
                        relief="flat")
        style.map('TCombobox',
                fieldbackground=[('readonly', COLORES.get("superficie3", "#2d3047"))],
                selectbackground=[('readonly', COLORES["accento"])],
                selectforeground=[('readonly', COLORES["texto"])])
        
        # Forzar actualización de todos los widgets
        self.root.update_idletasks()
        
        print("🎨 Interfaz actualizada con nuevos colores")
        
    def actualizar_colores_inputs(self):
        """Actualiza los colores de todos los inputs después de un cambio de tema"""
        try:
            # Actualizar estilo de combobox
            if hasattr(self, 'filtro_tipo'):
                self.filtro_tipo._actualizar_estilo()
            
            # Actualizar entrada_maquina si existe
            if hasattr(self, 'entrada_maquina'):
                self.entrada_maquina._actualizar_estilo()
            
            # Actualizar todos los widgets Entry en la ventana de configuración
            if hasattr(self, 'config_window') and self.config_window and self.config_window.winfo_exists():
                for widget in self.config_window.winfo_children():
                    self._actualizar_widget_recursivo(widget)
            
            print("✅ Colores de inputs actualizados")
        except Exception as e:
            print(f"Error actualizando inputs: {e}")

    def _actualizar_widget_recursivo(self, widget):
        """Actualiza recursivamente los colores de widgets"""
        try:
            if isinstance(widget, tk.Entry):
                # Actualizar Entry normal
                try:
                    widget.config(
                        bg=COLORES.get("superficie3", "#2d3047"),
                        fg=COLORES["texto"],
                        insertbackground=COLORES["texto"],
                        highlightbackground=COLORES["texto_secundario"],
                        highlightcolor=COLORES["accento"]
                    )
                except:
                    pass
            elif isinstance(widget, ttk.Combobox):
                # Intentar actualizar Combobox
                try:
                    style = ttk.Style()
                    style.configure("TCombobox",
                                    fieldbackground=COLORES.get("superficie3", "#2d3047"),
                                    background=COLORES.get("superficie3", "#2d3047"),
                                    foreground=COLORES["texto"])
                except:
                    pass
            elif isinstance(widget, tk.Text):
                try:
                    widget.config(
                        bg=COLORES.get("superficie3", "#2d3047"),
                        fg=COLORES["texto"]
                    )
                except:
                    pass
            
            # Procesar hijos
            for child in widget.winfo_children():
                self._actualizar_widget_recursivo(child)
        except:
            pass
        
        # ===== MÉTODOS DE DIAGNÓSTICO DE CONECTIVIDAD =====
        
    def diagnosticar_conectividad(self):
        """Prueba la conectividad a internet y al servidor de licencias"""
        import socket
        
        print("🔍 Diagnosticando conectividad...")
        resultados = []
        
        # 1. Probar conexión a internet (Google DNS)
        try:
            socket.gethostbyname("google.com")
            print("✅ Internet disponible")
            resultados.append("✅ Internet: OK")
        except:
            print("❌ Sin acceso a internet")
            resultados.append("❌ Internet: Falló")
            return False, resultados
        
        # 2. Probar resolución del servidor de licencias
        try:
            ip = socket.gethostbyname(LICENSE_DB_CONFIG["host"])
            print(f"✅ Servidor de licencias resuelto: {ip}")
            resultados.append(f"✅ DNS: {LICENSE_DB_CONFIG['host']} -> {ip}")
        except:
            print(f"❌ No se puede resolver {LICENSE_DB_CONFIG['host']}")
            resultados.append(f"❌ DNS: No se pudo resolver {LICENSE_DB_CONFIG['host']}")
            return False, resultados
        
        # 3. Probar puerto
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((LICENSE_DB_CONFIG["host"], LICENSE_DB_CONFIG["port"]))
            sock.close()
            
            if result == 0:
                print(f"✅ Puerto {LICENSE_DB_CONFIG['port']} accesible")
                resultados.append(f"✅ Puerto {LICENSE_DB_CONFIG['port']}: Abierto")
            else:
                print(f"❌ Puerto {LICENSE_DB_CONFIG['port']} bloqueado (código: {result})")
                resultados.append(f"❌ Puerto {LICENSE_DB_CONFIG['port']}: Bloqueado")
                return False, resultados
        except Exception as e:
            print(f"❌ Error probando puerto: {e}")
            resultados.append(f"❌ Puerto: Error - {str(e)}")
            return False, resultados
        
        # 4. Probar conexión MySQL real
        try:
            conn = mysql.connector.connect(
                host=LICENSE_DB_CONFIG["host"],
                port=LICENSE_DB_CONFIG["port"],
                user=LICENSE_DB_CONFIG["usuario"],
                password=LICENSE_DB_CONFIG["password"],
                database=LICENSE_DB_CONFIG["base_datos"],
                connection_timeout=5,
                ssl_disabled=not LICENSE_DB_CONFIG["usar_ssl"]
            )
            conn.close()
            print("✅ Conexión MySQL exitosa")
            resultados.append("✅ MySQL: Conexión exitosa")
        except Exception as e:
            print(f"❌ MySQL: Error de conexión - {e}")
            resultados.append(f"❌ MySQL: {str(e)[:50]}")
            return False, resultados
        
        return True, resultados

    def mostrar_diagnostico(self):
        """Muestra una ventana con el diagnóstico de conectividad"""
        exito, resultados = self.diagnosticar_conectividad()
        
        # Crear ventana de diagnóstico
        diag_window = tk.Toplevel(self.root)
        diag_window.title("Diagnóstico de Conectividad")
        diag_window.geometry("500x400")
        diag_window.configure(bg=COLORES["fondo"])
        
        tk.Label(diag_window, 
                text="📡 Diagnóstico de Red", 
                bg=COLORES["fondo"], 
                fg=COLORES["texto"],
                font=("Segoe UI", 16, "bold")).pack(pady=20)
        
        # Mostrar resultados
        frame = tk.Frame(diag_window, bg=COLORES["card"])
        frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        for i, resultado in enumerate(resultados):
            color = COLORES["success"] if "✅" in resultado else COLORES["danger"]
            tk.Label(frame, 
                    text=resultado,
                    bg=COLORES["card"],
                    fg=color,
                    font=("Segoe UI", 10),
                    anchor="w").pack(fill="x", padx=10, pady=2)
        
        # Botón cerrar
        tk.Button(diag_window,
                 text="Cerrar",
                 command=diag_window.destroy,
                 bg=COLORES["accento"],
                 fg=COLORES["texto"],
                 font=("Segoe UI", 10),
                 padx=20,
                 pady=5).pack(pady=20)
    
# ============================================================================
# ========== PUNTO DE ENTRADA ==========
# ============================================================================

if __name__ == "__main__":
    root = tk.Tk()
    app = AndonApp(root)
    root.mainloop()