# src/services/network_service.py

import socket
import threading
import queue
import logging
import time
from typing import Callable, Optional

logger = logging.getLogger(__name__)

class NetworkService:
    """Servicio para manejar la comunicación TCP con ESP32"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 5000):
        self.host = host
        self.port = port
        self.event_queue = queue.Queue(maxsize=10000)
        self.running = False
        self.callback: Optional[Callable] = None
        self.server_thread: Optional[threading.Thread] = None
        self.processor_thread: Optional[threading.Thread] = None

    def start(self, callback: Callable):
        """Inicia el servidor TCP y el procesador de cola"""
        self.callback = callback
        self.running = True
        
        self.processor_thread = threading.Thread(target=self._procesar_cola, daemon=True)
        self.processor_thread.start()
        
        self.server_thread = threading.Thread(target=self._servidor_tcp, daemon=True)
        self.server_thread.start()
        
        logger.info(f"Servidor de red iniciado en {self.host}:{self.port}")

    def stop(self):
        """Detiene el servicio"""
        self.running = False
        logger.info("Servicio de red detenido")

    def _servidor_tcp(self):
        """Bucle principal del servidor TCP"""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(200)
        
        while self.running:
            try:
                client, addr = server.accept()
                threading.Thread(target=self._manejador_cliente, 
                               args=(client, addr), 
                               daemon=True).start()
            except Exception as e:
                if self.running:
                    logger.error(f"Error en accept: {e}")
                    time.sleep(0.1)

    def _manejador_cliente(self, client_socket, addr):
        """Maneja una conexión de cliente individual"""
        try:
            client_socket.settimeout(5.0)
            data = client_socket.recv(64).decode().strip()
            if data and '|' in data:
                maquina, tipo = data.split('|', 1)
                try:
                    self.event_queue.put_nowait((maquina.strip(), tipo.strip()))
                except queue.Full:
                    logger.warning(f"Cola llena, descartando evento de {addr}")
            client_socket.close()
        except socket.timeout:
            logger.debug(f"⏱Timeout en conexión de {addr}")
        except Exception as e:
            logger.error(f"Error con cliente {addr}: {e}")
        finally:
            client_socket.close()

    def _procesar_cola(self):
        """Procesa eventos en lote cada 100ms"""
        batch = []
        last_process = time.time()
        
        while self.running:
            try:
                evento = self.event_queue.get(timeout=0.1)
                batch.append(evento)
                
                if len(batch) >= 10 or (time.time() - last_process) > 0.1:
                    if self.callback:
                        self.callback(batch.copy())
                    batch.clear()
                    last_process = time.time()
                    
            except queue.Empty:
                if batch and self.callback:
                    self.callback(batch.copy())
                    batch.clear()
                    last_process = time.time()
                continue
            except Exception as e:
                logger.error(f"Error procesando cola: {e}")