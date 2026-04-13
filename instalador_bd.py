# instalador_bd.py
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import hashlib
import os
import traceback
import time

# Obtener ruta del archivo de log (mismo que en instalador.py)
LOG_FILE = os.path.join(os.environ.get('TEMP', 'C:\\Temp'), 'andon_installer.log')

def log_instalador(mensaje, tipo="INFO"):
    """Guarda mensajes en el archivo de log del instalador"""
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] [{tipo}] {mensaje}\n")
    except:
        pass

def crear_tablas_mysql(config_mysql):
    """Crea TODAS las tablas con estructura COMPLETA en MySQL"""
    log_instalador(f"⚙️ Creando tablas en MySQL: {config_mysql['host']}/{config_mysql['base_datos']}")
    
    conn = None
    try:
        # Intentar conectar con timeout más largo
        log_instalador("   Conectando a MySQL...")
        conn = mysql.connector.connect(
            host=config_mysql["host"],
            port=config_mysql["port"],
            user=config_mysql["usuario"],
            password=config_mysql["password"],
            database=config_mysql["base_datos"],
            connection_timeout=60,
            ssl_disabled=not config_mysql.get("usar_ssl", False),
            use_pure=True,
            autocommit=False,
            buffered=True,
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci',
            get_warnings=True,
            raise_on_warnings=False
        )
        log_instalador("   ✅ Conexión establecida")
        
        cursor = conn.cursor()
        
        # Verificar conexión
        cursor.execute("SELECT 1")
        log_instalador("   ✅ Conexión verificada")
        
        # Verificar si las tablas ya existen
        cursor.execute("SHOW TABLES")
        tablas_existentes = [tabla[0] for tabla in cursor.fetchall()]
        log_instalador(f"   📋 Tablas existentes: {tablas_existentes}")
        
        # ===== CREAR TABLAS EN ORDEN CORRECTO =====
        
        # 1. Tabla demo_installations
        if 'demo_installations' not in tablas_existentes:
            log_instalador("   Creando tabla 'demo_installations'...")
            cursor.execute('''
                CREATE TABLE demo_installations (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    installation_id VARCHAR(50) NOT NULL UNIQUE,
                    ip_address VARCHAR(50),
                    started_at DATETIME NOT NULL,
                    expires_at DATE NOT NULL,
                    is_expired BOOLEAN DEFAULT FALSE,
                    created_at DATETIME,
                    INDEX idx_installation (installation_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            log_instalador("   ✅ Tabla 'demo_installations' creada")
        else:
            log_instalador("   ℹ️ Tabla 'demo_installations' ya existe")
        
        # 2. Tabla tipos_falla
        if 'tipos_falla' not in tablas_existentes:
            log_instalador("   Creando tabla 'tipos_falla'...")
            cursor.execute('''
                CREATE TABLE tipos_falla (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(100) NOT NULL UNIQUE,
                    color VARCHAR(20) NOT NULL,
                    orden INT DEFAULT 0
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            log_instalador("   ✅ Tabla 'tipos_falla' creada")
        else:
            log_instalador("   ℹ️ Tabla 'tipos_falla' ya existe")
        
        # 3. Tabla fallas_activas
        if 'fallas_activas' not in tablas_existentes:
            log_instalador("   Creando tabla 'fallas_activas'...")
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
            log_instalador("   ✅ Tabla 'fallas_activas' creada")
        else:
            log_instalador("   ℹ️ Tabla 'fallas_activas' ya existe")
        
        # 4. Tabla fallas (historial)
        if 'fallas' not in tablas_existentes:
            log_instalador("   Creando tabla 'fallas'...")
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
            log_instalador("   ✅ Tabla 'fallas' creada")
        else:
            log_instalador("   ℹ️ Tabla 'fallas' ya existe")
        
        # 5. Tabla config_sistema
        if 'config_sistema' not in tablas_existentes:
            log_instalador("   Creando tabla 'config_sistema'...")
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
            log_instalador("   ✅ Tabla 'config_sistema' creada")
        else:
            log_instalador("   ℹ️ Tabla 'config_sistema' ya existe")
        
        # 6. Tabla config_proyeccion
        if 'config_proyeccion' not in tablas_existentes:
            log_instalador("   Creando tabla 'config_proyeccion'...")
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
                    font_size INT DEFAULT 16,
                    CONSTRAINT chk_proyeccion_id CHECK (id = 1)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            log_instalador("   ✅ Tabla 'config_proyeccion' creada")
        else:
            log_instalador("   ℹ️ Tabla 'config_proyeccion' ya existe")
        
        # 7. Tabla config_contador
        if 'config_contador' not in tablas_existentes:
            log_instalador("   Creando tabla 'config_contador'...")
            cursor.execute('''
                CREATE TABLE config_contador (
                    id INT PRIMARY KEY,
                    ultimo_reset DATETIME NOT NULL,
                    consecutivo_actual INT DEFAULT 0,
                    periodo_reset VARCHAR(20) DEFAULT 'diario',
                    CONSTRAINT chk_contador_id CHECK (id = 1)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            log_instalador("   ✅ Tabla 'config_contador' creada")
        else:
            log_instalador("   ℹ️ Tabla 'config_contador' ya existe")
        
        # 8. Tabla config_licencia
        if 'config_licencia' not in tablas_existentes:
            log_instalador("   Creando tabla 'config_licencia'...")
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
            log_instalador("   ✅ Tabla 'config_licencia' creada")
        else:
            log_instalador("   ℹ️ Tabla 'config_licencia' ya existe")
        
        # 9. Tabla mapeo_botones
        if 'mapeo_botones' not in tablas_existentes:
            log_instalador("   Creando tabla 'mapeo_botones'...")
            cursor.execute('''
                CREATE TABLE mapeo_botones (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    numero_boton INT NOT NULL UNIQUE,
                    tipo_falla VARCHAR(100) NOT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            log_instalador("   ✅ Tabla 'mapeo_botones' creada")
        else:
            log_instalador("   ℹ️ Tabla 'mapeo_botones' ya existe")
        
        # 10. Tabla sonidos_falla
        if 'sonidos_falla' not in tablas_existentes:
            log_instalador("   Creando tabla 'sonidos_falla'...")
            cursor.execute('''
                CREATE TABLE sonidos_falla (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    tipo_falla VARCHAR(100) NOT NULL,
                    ruta_archivo VARCHAR(500) NOT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            # Crear índice único después de la tabla
            cursor.execute("CREATE UNIQUE INDEX idx_unique_tipo_falla ON sonidos_falla (tipo_falla)")
            log_instalador("   ✅ Tabla 'sonidos_falla' creada")
        else:
            log_instalador("   ℹ️ Tabla 'sonidos_falla' ya existe")
        
       
        
        # ===== INSERTAR DATOS POR DEFECTO =====
        
        # Insertar config_sistema si no existe
        cursor.execute("SELECT COUNT(*) FROM config_sistema WHERE id = 1")
        if cursor.fetchone()[0] == 0:
            log_instalador("   Insertando datos por defecto en config_sistema...")
            cursor.execute("INSERT INTO config_sistema (id) VALUES (1)")
            log_instalador("   ✅ Datos insertados en config_sistema")
        
        # Insertar config_proyeccion si no existe
        cursor.execute("SELECT COUNT(*) FROM config_proyeccion WHERE id = 1")
        if cursor.fetchone()[0] == 0:
            log_instalador("   Insertando datos por defecto en config_proyeccion...")
            cursor.execute("INSERT INTO config_proyeccion (id) VALUES (1)")
            log_instalador("   ✅ Datos insertados en config_proyeccion")
        
        # Insertar config_contador si no existe
        cursor.execute("SELECT COUNT(*) FROM config_contador WHERE id = 1")
        if cursor.fetchone()[0] == 0:
            log_instalador("   Insertando datos por defecto en config_contador...")
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO config_contador (id, ultimo_reset) VALUES (1, %s)", (ahora,))
            log_instalador("   ✅ Datos insertados en config_contador")
        
        # Insertar tipos de falla por defecto (solo si la tabla está vacía)
        cursor.execute("SELECT COUNT(*) FROM tipos_falla")
        if cursor.fetchone()[0] == 0:
            log_instalador("   Insertando tipos de falla por defecto...")
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
            log_instalador("   ✅ Tipos de falla insertados")
        
        conn.commit()
        log_instalador("   ✅ Todas las operaciones completadas correctamente")
        return True, "Base de datos MySQL inicializada correctamente"
    
    except mysql.connector.Error as e:
        error_msg = str(e)
        log_instalador(f"   ❌ Error de MySQL: {error_msg}", "ERROR")
        log_instalador(f"   Código de error: {e.errno if hasattr(e, 'errno') else 'N/A'}", "ERROR")
        
        if conn:
            try:
                conn.rollback()
            except:
                pass
        
        return False, f"Error MySQL ({e.errno}): {error_msg}"
    
    except Exception as e:
        error_msg = str(e)
        log_instalador(f"   ❌ Error general: {error_msg}", "ERROR")
        log_instalador(f"   Tipo de error: {type(e).__name__}", "ERROR")
        log_instalador(traceback.format_exc(), "ERROR")
        
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
                log_instalador("   Conexión cerrada")
            except:
                pass