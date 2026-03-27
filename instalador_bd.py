# instalador_bd.py
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import hashlib
import os
import traceback
import time

def crear_tablas_mysql(config_mysql):
    """Crea TODAS las tablas con estructura COMPLETA en MySQL"""
    print(f"⚙️ Creando tablas en MySQL: {config_mysql['host']}/{config_mysql['base_datos']}")
    
    conn = None
    try:
        # Intentar conectar con timeout más largo y usando implementación pura
        print("   Conectando a MySQL...")
        conn = mysql.connector.connect(
            host=config_mysql["host"],
            port=config_mysql["port"],
            user=config_mysql["usuario"],
            password=config_mysql["password"],
            database=config_mysql["base_datos"],
            connection_timeout=60,  # Timeout más largo
            ssl_disabled=not config_mysql["usar_ssl"],
            use_pure=True,  # Forzar implementación pura de Python
            autocommit=False,
            buffered=True,
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci',
            get_warnings=True,
            raise_on_warnings=False
        )
        print("   ✅ Conexión establecida")
        
        cursor = conn.cursor()
        
        # Verificar conexión
        cursor.execute("SELECT 1")
        print("   ✅ Conexión verificada")
        
        # Verificar si las tablas ya existen
        cursor.execute("SHOW TABLES")
        tablas_existentes = [tabla[0] for tabla in cursor.fetchall()]
        print(f"   📋 Tablas existentes: {tablas_existentes}")
        
        if 'demo_installations' not in tablas_existentes:
            print("   Creando tabla 'demo_installations'...")
            cursor.execute('''
                CREATE TABLE demo_installations (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    installation_id VARCHAR(50) NOT NULL UNIQUE,
                    started_at DATETIME NOT NULL,
                    expires_at DATE NOT NULL,
                    INDEX idx_installation (installation_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            print("   ✅ Tabla 'demo_installations' creada")
        else:
            print("   ℹ️ Tabla 'demo_installations' ya existe")
            
        
        # --- Tabla de Sonidos por Tipo de Falla ---
        if 'sonidos_falla' not in tablas_existentes:
            print("   Creando tabla 'sonidos_falla'...")
            cursor.execute('''
                CREATE TABLE sonidos_falla (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    tipo_falla VARCHAR(100) NOT NULL UNIQUE,
                    ruta_archivo VARCHAR(500) NOT NULL,
                    UNIQUE KEY unique_tipo_falla (tipo_falla)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            print("   ✅ Tabla 'sonidos_falla' creada")
        else:
            print("   ℹ️ Tabla 'sonidos_falla' ya existe")

        # --- Tabla de fallas (historial) ---
        if 'fallas' not in tablas_existentes:
            print("   Creando tabla 'fallas'...")
            cursor.execute('''
                CREATE TABLE fallas (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    maquina VARCHAR(50) NOT NULL,
                    tipo VARCHAR(100) NOT NULL,
                    inicio DATETIME NOT NULL,
                    proceso DATETIME,
                    fin DATETIME,
                    t_inicio_proceso VARCHAR(20),
                    t_proceso_fin VARCHAR(20),
                    t_total VARCHAR(20),
                    numero_falla INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    estado VARCHAR(20) DEFAULT 'activa',
                    nota_pendiente TEXT,
                    fecha_pendiente DATETIME,
                    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_numero_falla (numero_falla)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            print("   ✅ Tabla 'fallas' creada")
        else:
            print("   ℹ️ Tabla 'fallas' ya existe")
        
        # --- Tabla de fallas activas ---
        if 'fallas_activas' not in tablas_existentes:
            print("   Creando tabla 'fallas_activas'...")
            cursor.execute('''
                CREATE TABLE fallas_activas (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    maquina VARCHAR(50) NOT NULL,
                    tipo VARCHAR(100) NOT NULL,
                    inicio DATETIME NOT NULL,
                    proceso DATETIME,
                    fin DATETIME,
                    numero_falla INT UNIQUE,
                    estado VARCHAR(20) DEFAULT 'activa',
                    nota_pendiente TEXT,
                    fecha_pendiente DATETIME,
                    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_numero_falla (numero_falla)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            print("   ✅ Tabla 'fallas_activas' creada")
        else:
            print("   ℹ️ Tabla 'fallas_activas' ya existe")
        
        # --- Tabla de tipos de falla ---
        if 'tipos_falla' not in tablas_existentes:
            print("   Creando tabla 'tipos_falla'...")
            cursor.execute('''
                CREATE TABLE tipos_falla (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(100) NOT NULL UNIQUE,
                    color VARCHAR(20) NOT NULL,
                    orden INT DEFAULT 0
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            print("   ✅ Tabla 'tipos_falla' creada")
        else:
            print("   ℹ️ Tabla 'tipos_falla' ya existe")
        
        # --- Tabla de configuración del sistema ---
        if 'config_sistema' not in tablas_existentes:
            print("   Creando tabla 'config_sistema'...")
            cursor.execute('''
                CREATE TABLE config_sistema (
                    id INT PRIMARY KEY,
                    nombre_sistema VARCHAR(100) DEFAULT 'ANDON SYSTEM',
                    tema_activo VARCHAR(20) DEFAULT 'oscuro',
                    color_fondo VARCHAR(20) DEFAULT '#1a1a2e',
                    color_sidebar VARCHAR(20) DEFAULT '#16213e',
                    color_card VARCHAR(20) DEFAULT '#0f3460',
                    superficie3 VARCHAR(20) DEFAULT '#2d3047',
                    color_texto VARCHAR(20) DEFAULT '#ffffff',
                    texto_principal VARCHAR(20) DEFAULT '#ffffff',
                    color_texto_secundario VARCHAR(20) DEFAULT '#b0b0b0',
                    texto_secundario VARCHAR(20) DEFAULT '#b0b0b0',
                    color_acento VARCHAR(20) DEFAULT '#e94560',
                    acento_principal VARCHAR(20) DEFAULT '#e94560',
                    color_exito VARCHAR(20) DEFAULT '#00C853',
                    exito VARCHAR(20) DEFAULT '#00C853',
                    color_warning VARCHAR(20) DEFAULT '#FFC107',
                    advertencia VARCHAR(20) DEFAULT '#FFC107',
                    color_danger VARCHAR(20) DEFAULT '#FF5252',
                    peligro VARCHAR(20) DEFAULT '#FF5252',
                    color_pendiente VARCHAR(20) DEFAULT '#FFA500',
                    pendiente VARCHAR(20) DEFAULT '#FFA500',
                    CONSTRAINT chk_sistema_id CHECK (id = 1)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            print("   ✅ Tabla 'config_sistema' creada")
        else:
            print("   ℹ️ Tabla 'config_sistema' ya existe")
        
        # --- Tabla de configuración de proyección ---
        if 'config_proyeccion' not in tablas_existentes:
            print("   Creando tabla 'config_proyeccion'...")
            cursor.execute('''
                CREATE TABLE config_proyeccion (
                    id INT PRIMARY KEY,
                    pantalla_completa BOOLEAN DEFAULT FALSE,
                    recordar_posicion BOOLEAN DEFAULT TRUE,
                    x INT DEFAULT 100,
                    y INT DEFAULT 100,
                    ancho INT DEFAULT 800,
                    alto INT DEFAULT 600,
                    monitor INT DEFAULT 0,
                    color_fondo VARCHAR(20) DEFAULT '#000000',
                    mostrar_contador BOOLEAN DEFAULT TRUE,
                    color_texto VARCHAR(20) DEFAULT '#FFFFFF',
                    color_acento VARCHAR(20) DEFAULT '#e94560',
                    color_exito VARCHAR(20) DEFAULT '#4CAF50',
                    mostrar_pendientes BOOLEAN DEFAULT TRUE,
                    CONSTRAINT chk_proyeccion_id CHECK (id = 1)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            print("   ✅ Tabla 'config_proyeccion' creada")
        else:
            print("   ℹ️ Tabla 'config_proyeccion' ya existe")
        
        # --- Tabla de configuración de contador ---
        if 'config_contador' not in tablas_existentes:
            print("   Creando tabla 'config_contador'...")
            cursor.execute('''
                CREATE TABLE config_contador (
                    id INT PRIMARY KEY,
                    ultimo_reset DATETIME NOT NULL,
                    consecutivo_actual INT DEFAULT 0,
                    periodo_reset VARCHAR(20) DEFAULT 'diario',
                    CONSTRAINT chk_contador_id CHECK (id = 1)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            print("   ✅ Tabla 'config_contador' creada")
        else:
            print("   ℹ️ Tabla 'config_contador' ya existe")
        
        # --- Tabla de licencia ---
        if 'config_licencia' not in tablas_existentes:
            print("   Creando tabla 'config_licencia'...")
            cursor.execute('''
                CREATE TABLE config_licencia (
                    id INT PRIMARY KEY,
                    installation_id VARCHAR(50) NOT NULL,
                    license_key VARCHAR(100),
                    license_type VARCHAR(20) DEFAULT 'basic',
                    demo_used BOOLEAN DEFAULT FALSE,
                    demo_start DATETIME,
                    demo_expires DATE,
                    max_fallas INT DEFAULT 3,
                    max_maquinas INT DEFAULT 5,
                    last_validation DATETIME,
                    grace_period_start DATETIME,
                    excel_exports_today INT DEFAULT 0,
                    last_export_date DATE,
                    expires_at DATE,
                    CONSTRAINT chk_licencia_id CHECK (id = 1)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            print("   ✅ Tabla 'config_licencia' creada")
        else:
            print("   ℹ️ Tabla 'config_licencia' ya existe")
        
        # --- Tabla Mapeo de Botones ---
        if 'mapeo_botones' not in tablas_existentes:
            print("   Creando tabla 'mapeo_botones'...")
            cursor.execute('''
                CREATE TABLE mapeo_botones (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    numero_boton INT NOT NULL UNIQUE,
                    tipo_falla VARCHAR(100) NOT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            print("   ✅ Tabla 'mapeo_botones' creada")
        else:
            print("   ℹ️ Tabla 'mapeo_botones' ya existe")
        
        # ===== INSERTAR DATOS POR DEFECTO =====
        
        # Insertar config_sistema si no existe
        cursor.execute("SELECT COUNT(*) FROM config_sistema WHERE id = 1")
        if cursor.fetchone()[0] == 0:
            print("   Insertando datos por defecto en config_sistema...")
            cursor.execute("INSERT INTO config_sistema (id) VALUES (1)")
            print("   ✅ Datos insertados en config_sistema")
        
        # Insertar config_proyeccion si no existe
        cursor.execute("SELECT COUNT(*) FROM config_proyeccion WHERE id = 1")
        if cursor.fetchone()[0] == 0:
            print("   Insertando datos por defecto en config_proyeccion...")
            cursor.execute("INSERT INTO config_proyeccion (id) VALUES (1)")
            print("   ✅ Datos insertados en config_proyeccion")
        
        # Insertar config_contador si no existe
        cursor.execute("SELECT COUNT(*) FROM config_contador WHERE id = 1")
        if cursor.fetchone()[0] == 0:
            print("   Insertando datos por defecto en config_contador...")
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO config_contador (id, ultimo_reset) VALUES (1, %s)", (ahora,))
            print("   ✅ Datos insertados en config_contador")
        
        # Insertar tipos de falla por defecto (solo si la tabla está vacía)
        cursor.execute("SELECT COUNT(*) FROM tipos_falla")
        if cursor.fetchone()[0] == 0:
            print("   Insertando tipos de falla por defecto...")
            tipos_default = [
                ("Mantenimiento", "#FF9A00", 1),
                ("Producción", "#FF5252", 2),
                ("Calidad", "#4CAF50", 3),
                ("Materiales", "#2196F3", 4),
                ("Ingeniería", "#9C27B0", 5)
            ]
            for nombre, color, orden in tipos_default:
                cursor.execute("INSERT INTO tipos_falla (nombre, color, orden) VALUES (%s, %s, %s)",
                              (nombre, color, orden))
            print("   ✅ Tipos de falla insertados")
        
        conn.commit()
        print("   ✅ Todas las operaciones completadas correctamente")
        return True, "Base de datos MySQL inicializada correctamente"
    
    except mysql.connector.Error as e:
        error_msg = str(e)
        print(f"   ❌ Error de MySQL: {error_msg}")
        print(f"   Código de error: {e.errno if hasattr(e, 'errno') else 'N/A'}")
        print(f"   SQL State: {e.sqlstate if hasattr(e, 'sqlstate') else 'N/A'}")
        traceback.print_exc()
        
        if conn:
            try:
                conn.rollback()
            except:
                pass
        
        return False, f"Error MySQL ({e.errno}): {error_msg}"
    
    except Exception as e:
        error_msg = str(e)
        print(f"   ❌ Error general: {error_msg}")
        print(f"   Tipo de error: {type(e).__name__}")
        traceback.print_exc()
        
        if conn:
            try:
                conn.rollback()
            except:
                pass
        
        return False, f"Error inesperado: {error_msg}"
    
    finally:
        if conn:
            try:
                conn.close()
                print("   Conexión cerrada")
            except:
                pass