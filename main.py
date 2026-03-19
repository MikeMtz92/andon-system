# main.py

"""
Punto de entrada principal del sistema Andon
"""

import os
import sys
import socket
import threading

# ===== BLOQUEO DE INSTANCIA ÚNICA =====
def verificar_instancia_unica():
    """Verifica que solo haya una instancia del programa ejecutándose"""
    lock_port = 54321
    lock_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try:
        lock_socket.bind(('127.0.0.1', lock_port))
        return True, lock_socket
    except socket.error:
        return False, None

def activar_ventana_existente():
    """Intenta activar la ventana de la otra instancia"""
    try:
        notify_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        notify_socket.settimeout(2)
        notify_socket.sendto(b'ACTIVATE', ('127.0.0.1', 54322))
        notify_socket.close()
    except:
        pass

def main():
    """Función principal"""
    # Verificar instancia única
    es_unica, lock_socket = verificar_instancia_unica()
    
    if not es_unica:
        print("⚠️ El programa ya está en ejecución")
        activar_ventana_existente()
        sys.exit(0)
    
    # Verificar si es primera instalación
    if not os.path.exists("db_config.json"):
        # Primera instalación - ejecutar instalador
        from instalador import InstaladorAndon
        InstaladorAndon()
    else:
        # Ya instalado - ejecutar aplicación principal
        from src.main import main as app_main
        app_main()

if __name__ == "__main__":
    main()