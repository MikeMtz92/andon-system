# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('src', 'src'), ('recursos', 'recursos')]
binaries = []
hiddenimports = ['instalador', 'instalador_bd', 'src', 'src.main', 'src.controllers', 'src.controllers.app_controller', 'src.controllers.falla_controller', 'src.controllers.licencia_controller', 'src.models', 'src.models.config_model', 'src.models.database', 'src.models.falla_model', 'src.models.licencia_model', 'src.models.sound_model', 'src.models.torreta_model', 'src.services', 'src.services.excel_service', 'src.services.network_service', 'src.services.serial_service', 'src.services.theme_service', 'src.services.sound_service', 'src.utils', 'src.utils.constants', 'src.utils.helpers', 'src.utils.widgets', 'src.views', 'src.views.andon_view', 'src.views.config_view', 'src.views.esp32_view', 'src.views.estadisticas_view', 'src.views.historial_view', 'src.views.licencia_view', 'src.views.main_view', 'src.views.pendientes_view', 'src.views.proyeccion_config_view', 'src.views.proyeccion_view', 'mysql.connector', 'mysql.connector.connection', 'mysql.connector.cursor', 'mysql.connector.cursor_cext', 'mysql.connector.pooling', 'mysql.connector.locales', 'mysql.connector.locales.eng', 'mysql.connector.errorcode', 'mysql.connector.errors', 'pandas', 'openpyxl', 'matplotlib', 'matplotlib.backends.backend_tkagg', 'matplotlib.pyplot', 'tkcalendar', 'serial', 'serial.tools.list_ports', 'psutil', 'screeninfo', 'pygame', 'pygame.mixer', 'socket', 'ssl', 'queue', 'threading', 'time', 'datetime', 'hashlib', 'json', 'os', 'sys', 'atexit', 'signal', 'winsound', 'colorsys', 'io']
tmp_ret = collect_all('mysql.connector')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('pandas')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('matplotlib')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('pygame')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['main.py'],
    pathex=['.', 'src'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ReActionAndon',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',
    icon=['recursos\\icono.ico'],
)
