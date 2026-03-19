# main.py
import os
import sys
import json
import socket
import threading

# ===== BLOQUEO DE INSTANCIA ÚNICA =====
def verificar_instancia_unica():
    """
    Verifica que solo haya una instancia del programa ejecutándose.
    Usa un socket para crear un lock a nivel de sistema.
    """
    lock_port = 54321  # Puerto arbitrario para el lock
    lock_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try:
        # Intentar enlazar el socket a una dirección local
        # Esto fallará si otra instancia ya lo tiene enlazado
        lock_socket.bind(('127.0.0.1', lock_port))
        # Si tiene éxito, guardamos el socket para mantener el lock
        return True, lock_socket
    except socket.error:
        # Error de socket: otra instancia ya está enlazada
        return False, None

# Función para activar la ventana existente
def activar_ventana_existente():
    """Intenta activar la ventana de la otra instancia"""
    try:
        # Intentar conectar al socket de la otra instancia
        notify_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        notify_socket.settimeout(2)
        notify_socket.sendto(b'ACTIVATE', ('127.0.0.1', 54322))  # Puerto para notificaciones
        notify_socket.close()
    except:
        pass

# Variable global para el socket de lock
lock_socket_global = None

# ===== FIN DE BLOQUEO DE INSTANCIA =====


def main():
    global lock_socket_global
    
    # Verificar si ya hay otra instancia ejecutándose
    es_unica, lock_socket = verificar_instancia_unica()
    
    if not es_unica:
        # Ya hay otra instancia ejecutándose
        print("⚠️ El programa ya está en ejecución")
        
        # ⚠️ IMPORTANTE: tkinter NO está importado todavía
        # Así que no podemos usarlo aquí directamente
        
        # En su lugar, mostramos un mensaje en consola y salimos
        print("Cerrando esta instancia para evitar problemas con la base de datos.")
        
        # Intentar activar la ventana existente
        activar_ventana_existente()
        
        # Salir sin usar tkinter
        sys.exit(0)
    else:
        # Primera instancia: guardar el socket para mantener el lock
        lock_socket_global = lock_socket
        print("✅ Primera instancia iniciada")
        
        # Iniciar hilo para escuchar notificaciones de activación
        def escuchar_activacion():
            try:
                notify_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                notify_socket.bind(('127.0.0.1', 54322))
                notify_socket.settimeout(1)
                
                while True:
                    try:
                        data, addr = notify_socket.recvfrom(1024)
                        if data == b'ACTIVATE':
                            # Activar la ventana - AHORA SÍ podemos usar tkinter
                            # porque este código se ejecuta después de que la app ya inició
                            try:
                                import tkinter as tk
                                # Buscar la ventana principal y traerla al frente
                                def traer_al_frente():
                                    try:
                                        # Obtener la ventana raíz
                                        if tk._default_root:
                                            tk._default_root.lift()
                                            tk._default_root.focus_force()
                                    except:
                                        pass
                                
                                # Ejecutar en el hilo principal
                                if tk._default_root:
                                    tk._default_root.after(0, traer_al_frente)
                            except:
                                pass
                    except socket.timeout:
                        continue
                    except:
                        break
            except:
                pass
        
        threading.Thread(target=escuchar_activacion, daemon=True).start()

    # ===== DESPUÉS de la verificación, importamos tkinter =====
    import tkinter as tk
    from tkinter import messagebox
    import sqlite3

    # Resto de tu código normal...
    if not os.path.exists("db_config.json"):
        # Primera instalación
        from instalador import InstaladorAndon
        InstaladorAndon()
    else:
        try:
            # Cargar configuración existente
            from ReAction import (AndonApp, cargar_config_licencia, cargar_config_db, 
                                 cargar_tipos_falla, cargar_config_sistema)
            
            db_config = cargar_config_db()
            licencia_config = cargar_config_licencia(db_config)
            tipos_falla_data = cargar_tipos_falla(db_config)
            config_sistema = cargar_config_sistema(db_config)
            
            root = tk.Tk()
            app = AndonApp(root, {
                'db_config': db_config,
                'licencia_config': licencia_config,
                'tipos_falla_data': tipos_falla_data,
                'config_sistema': config_sistema
            })
            root.mainloop()
            
        except Exception as e:
            print(f"❌ Error al iniciar aplicación: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error Crítico", 
                                f"No se pudo iniciar la aplicación:\n{str(e)}")

if __name__ == "__main__":
    main()