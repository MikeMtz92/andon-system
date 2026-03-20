# src/services/serial_service.py

import serial
import serial.tools.list_ports
import threading
import logging
import time
from typing import Optional, Callable

logger = logging.getLogger(__name__)

class SerialService:
    """Servicio para comunicación serial con ESP32"""
    
    def __init__(self):
        self.running = False
        self.callback: Optional[Callable] = None
        self.thread: Optional[threading.Thread] = None

    def start(self, callback: Callable):
        """Inicia la lectura serial"""
        self.callback = callback
        self.running = True
        self.thread = threading.Thread(target=self._leer_serial, daemon=True)
        self.thread.start()
        logger.info(" Servicio serial iniciado")

    def stop(self):
        """Detiene la lectura serial"""
        self.running = False
        logger.info("Servicio serial detenido")

    def _buscar_puerto(self) -> Optional[str]:
        """Busca un puerto serial compatible con ESP32"""
        for port in serial.tools.list_ports.comports():
            if "CP210" in port.description or "Silicon" in port.description:
                return port.device
        return None

    def _leer_serial(self):
        """Bucle principal de lectura serial"""
        puerto = self._buscar_puerto()
        if not puerto:
            logger.warning("ESP32 no detectado")
            return
        
        try:
            with serial.Serial(puerto, 115200, timeout=1) as ser:
                logger.info(f"Conectado a {puerto}")
                while self.running:
                    try:
                        linea = ser.readline().decode("utf-8").strip()
                        if linea and self.callback:
                            partes = linea.split("|")
                            if len(partes) == 2:
                                self.callback(partes[0].strip(), partes[1].strip())
                    except Exception as e:
                        logger.error(f"Error leyendo serial: {e}")
                        time.sleep(0.1)
        except Exception as e:
            logger.error(f"Error abriendo puerto serial: {e}")