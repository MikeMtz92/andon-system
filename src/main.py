# src/main.py

import tkinter as tk
from tkinter import messagebox
import sys
import os
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('andon.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Añadir directorio padre al path para importaciones
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.controllers.app_controller import AppController
from src.views.main_view import MainView

def main():
    """Punto de entrada principal de la aplicación"""
    try:
        # Crear controlador principal
        controller = AppController()
        
        # Inicializar componentes
        if not controller.initialize():
            logger.error("No se pudo inicializar el controlador")
            messagebox.showerror("Error Crítico", 
                               "No se pudo inicializar la aplicación.\n"
                               "Revisa el archivo de log para más detalles.")
            return
        
        # Verificar licencia
        if not controller.licencia_controller.licencia_valida:
            logger.warning("Licencia no válida, mostrando ventana de activación")
            # Aquí iría la lógica para mostrar ventana de activación si es necesario
        
        # Iniciar servicios
        controller.start_services()
        
        # Crear ventana principal
        root = tk.Tk()
        main_view = MainView(root, controller, controller.theme_service, 
                           controller.falla_controller)
        controller.main_view = main_view
        
        # Iniciar loop principal
        root.mainloop()
        
    except Exception as e:
        logger.exception("Error fatal en la aplicación")
        messagebox.showerror("Error Fatal", 
                           f"Error inesperado: {str(e)}\n\n"
                           "La aplicación se cerrará.")

if __name__ == "__main__":
    main()