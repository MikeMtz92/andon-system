@echo off
title COMPILADOR REACTION ANDON SYSTEM
color 0A
cls

echo ========================================
echo    COMPILADOR DE REACTION ANDON SYSTEM
echo ========================================
echo.
echo Este script compilara REACTION ANDON con estructura MVC
echo.

:: Verificar que estamos en la carpeta correcta
if not exist "src" (
    echo ERROR: No se encuentra la carpeta 'src'
    echo.
    pause
    exit /b 1
)

echo [1/5] Limpiando compilaciones anteriores...
if exist "dist" rmdir /s /q "dist" 2>nul
if exist "build" rmdir /s /q "build" 2>nul
if exist "*.spec" del /f /q *.spec 2>nul
echo OK
echo.

echo [2/5] Verificando dependencias...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Instalando PyInstaller...
    pip install pyinstaller
)

:: Instalar/actualizar dependencias
echo Instalando dependencias necesarias...
pip install --upgrade mysql-connector-python pandas openpyxl matplotlib tkcalendar pyserial psutil screeninfo requests certifi pygame
echo OK
echo.

echo [3/5] Compilando ReAction Andon System...
echo.

:: Compilar con main.py raíz como punto de entrada
pyinstaller --onefile --windowed ^
    --name="ReActionAndon" ^
    --icon=recursos\icono.ico ^
    --version-file=version_info.txt ^
    --add-data "src;src" ^
    --add-data "recursos;recursos" ^
    --paths . ^
    --paths src ^
    --hidden-import instalador ^
    --hidden-import instalador_bd ^
    --hidden-import src ^
    --hidden-import src.main ^
    --hidden-import src.controllers ^
    --hidden-import src.controllers.app_controller ^
    --hidden-import src.controllers.falla_controller ^
    --hidden-import src.controllers.licencia_controller ^
    --hidden-import src.models ^
    --hidden-import src.models.config_model ^
    --hidden-import src.models.database ^
    --hidden-import src.models.falla_model ^
    --hidden-import src.models.licencia_model ^
    --hidden-import src.models.sound_model ^
    --hidden-import src.models.torreta_model ^
    --hidden-import src.services ^
    --hidden-import src.services.excel_service ^
    --hidden-import src.services.network_service ^
    --hidden-import src.services.serial_service ^
    --hidden-import src.services.theme_service ^
    --hidden-import src.services.sound_service ^
    --hidden-import src.utils ^
    --hidden-import src.utils.constants ^
    --hidden-import src.utils.helpers ^
    --hidden-import src.utils.widgets ^
    --hidden-import src.views ^
    --hidden-import src.views.andon_view ^
    --hidden-import src.views.config_view ^
    --hidden-import src.views.esp32_view ^
    --hidden-import src.views.estadisticas_view ^
    --hidden-import src.views.historial_view ^
    --hidden-import src.views.licencia_view ^
    --hidden-import src.views.main_view ^
    --hidden-import src.views.pendientes_view ^
    --hidden-import src.views.proyeccion_config_view ^
    --hidden-import src.views.proyeccion_view ^
    --hidden-import mysql.connector ^
    --hidden-import mysql.connector.connection ^
    --hidden-import mysql.connector.cursor ^
    --hidden-import mysql.connector.cursor_cext ^
    --hidden-import mysql.connector.pooling ^
    --hidden-import mysql.connector.locales ^
    --hidden-import mysql.connector.locales.eng ^
    --hidden-import mysql.connector.errorcode ^
    --hidden-import mysql.connector.errors ^
    --hidden-import pandas ^
    --hidden-import openpyxl ^
    --hidden-import matplotlib ^
    --hidden-import matplotlib.backends.backend_tkagg ^
    --hidden-import matplotlib.pyplot ^
    --hidden-import tkcalendar ^
    --hidden-import serial ^
    --hidden-import serial.tools.list_ports ^
    --hidden-import psutil ^
    --hidden-import screeninfo ^
    --hidden-import pygame ^
    --hidden-import pygame.mixer ^
    --hidden-import socket ^
    --hidden-import ssl ^
    --hidden-import queue ^
    --hidden-import threading ^
    --hidden-import time ^
    --hidden-import datetime ^
    --hidden-import hashlib ^
    --hidden-import json ^
    --hidden-import os ^
    --hidden-import sys ^
    --hidden-import atexit ^
    --hidden-import signal ^
    --hidden-import winsound ^
    --hidden-import colorsys ^
    --hidden-import io ^
    --collect-all mysql.connector ^
    --collect-all pandas ^
    --collect-all matplotlib ^
    --collect-all pygame ^
    main.py

if errorlevel 1 (
    echo.
    echo ERROR: Fallo la compilacion!
    echo.
    pause
    exit /b 1
)

echo.
echo [4/5] Compilacion completada!
echo.

:: Crear carpeta de instalador
if not exist "instalador" mkdir instalador

:: Copiar el ejecutable
echo [5/5] Preparando archivos para instalador...
if exist "dist\ReActionAndon.exe" (
    copy "dist\ReActionAndon.exe" "instalador\" /Y
    echo OK: ReActionAndon.exe copiado a carpeta instalador
) else (
    echo ERROR: No se encontro el ejecutable en dist
    pause
    exit /b 1
)

:: Copiar recursos
if exist "recursos\icono.ico" (
    copy "recursos\icono.ico" "instalador\" /Y
    echo OK: icono.ico copiado
)

if exist "README.txt" (
    copy "README.txt" "instalador\" /Y
    echo OK: README.txt copiado
)

echo.
echo ========================================
echo    COMPILACION EXITOSA!
echo ========================================
echo.
echo EJECUTABLE: instalador\ReActionAndon.exe
echo.
echo Tamaño del archivo:
dir "instalador\ReActionAndon.exe"
echo.
pause