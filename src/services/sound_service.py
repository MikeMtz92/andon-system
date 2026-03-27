# src/services/sound_service.py

import logging
import threading
import os
import time
import pygame
import winsound  # Como fallback para WAV

logger = logging.getLogger(__name__)

class SoundService:
    """Servicio para reproducir sonidos de alarma de forma asíncrona"""

    def __init__(self):
        self._pygame_available = False
        try:
            pygame.mixer.init()
            self._pygame_available = True
            logger.info("Pygame mixer inicializado correctamente.")
        except Exception as e:
            logger.warning(f"No se pudo inicializar pygame, usando winsound para WAV: {e}")

    def play_sound(self, file_path: str):
        """Reproduce un archivo de sonido en un hilo separado"""
        if not file_path or not os.path.exists(file_path):
            logger.warning(f"Archivo de sonido no encontrado: {file_path}")
            return

        # Ejecutar la reproducción en un hilo para no bloquear la UI
        thread = threading.Thread(target=self._play, args=(file_path,), daemon=True)
        thread.start()

    def _play(self, file_path: str):
        """Método interno que realiza la reproducción"""
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if self._pygame_available:
                # Usar pygame para MP3, WAV, etc.
                logger.debug(f"Reproduciendo con pygame: {file_path}")
                sound = pygame.mixer.Sound(file_path)
                sound.play()
                # Esperar a que termine, pero sin bloquear el hilo principal de Tkinter
                # La espera ocurre en este hilo secundario, es correcto.
                while pygame.mixer.get_busy():
                    time.sleep(0.1)
            elif file_ext == '.wav':
                # Fallback a winsound solo para WAV
                logger.debug(f"Reproduciendo con winsound: {file_path}")
                winsound.PlaySound(file_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                # No espera, el sonido es asíncrono con winsound
            else:
                logger.warning(f"Formato no soportado sin pygame: {file_ext}. Instala pygame para reproducir MP3.")
        except Exception as e:
            logger.error(f"Error reproduciendo sonido {file_path}: {e}")