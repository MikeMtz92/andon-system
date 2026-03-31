# simulador_carga_andon.py
"""
Simulador de Carga para Sistema Andon - VERSIÓN CORREGIDA
Envia eventos en formato correcto: "maquina|BotonX"
El mapeo a tipos de falla se realiza en el servidor Andon
"""

import socket
import threading
import time
import random
import argparse
from datetime import datetime
import signal
import sys
from collections import defaultdict
import tkinter as tk
from tkinter import ttk, messagebox
import queue

# ========== CONFIGURACIÓN ==========
HOST = "localhost"
PORT = 5000

# Tipos de falla disponibles en el sistema (para referencia, no se envían directamente)
TIPOS_FALLA = [
    "Mantenimiento",
    "Producción", 
    "Calidad",
    "Materiales",
    "Ingeniería"
]

COLORES = {
    "fondo": "#1a1a2e",
    "card": "#16213e",
    "accento": "#e94560",
    "texto": "#ffffff",
    "exito": "#4CAF50",
    "warning": "#FFC107",
    "danger": "#FF5252"
}

class TerminalAndon:
    """Simula una terminal ESP32 individual"""
    
    def __init__(self, terminal_id, server_host, server_port, botones_por_terminal=5):
        self.maquina = str(terminal_id)
        self.server_host = server_host
        self.server_port = server_port
        self.botones_por_terminal = botones_por_terminal
        self.fallas_enviadas = 0
        self.conexiones_exitosas = 0
        self.conexiones_fallidas = 0
        self.latencia_total = 0
        self.ultima_latencia = 0
        
        print(f"✅ Terminal {self.maquina} creada - Botones disponibles: 1-{botones_por_terminal}")
    
    def enviar_falla(self, boton_especifico=None):
        """
        Envía una falla al servidor Andon
        Formato correcto: "maquina|BotonX"
        Donde X es el número de botón (1-5 normalmente)
        """
        if boton_especifico:
            boton = boton_especifico
        else:
            boton = random.randint(1, self.botones_por_terminal)
        
        # Formato correcto: máquina|BotonX
        mensaje = f"{self.maquina}|Boton{boton}\n"
        
        print(f"📤 Terminal {self.maquina} enviando: {mensaje.strip()}")
        
        start_time = time.time()
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            sock.connect((self.server_host, self.server_port))
            sock.send(mensaje.encode())
            
            self.conexiones_exitosas += 1
            self.fallas_enviadas += 1
            latencia = (time.time() - start_time) * 1000
            self.latencia_total += latencia
            self.ultima_latencia = latencia
            
            print(f"✅ Terminal {self.maquina} - OK ({latencia:.1f}ms)")
            return True, latencia, boton
            
        except socket.timeout:
            self.conexiones_fallidas += 1
            print(f"⏱️ Terminal {self.maquina} - TIMEOUT")
            return False, None, boton
        except ConnectionRefusedError:
            self.conexiones_fallidas += 1
            print(f"❌ Terminal {self.maquina} - CONEXIÓN RECHAZADA")
            return False, None, boton
        except Exception as e:
            self.conexiones_fallidas += 1
            print(f"❌ Terminal {self.maquina} - ERROR: {e}")
            return False, None, boton
        finally:
            if sock:
                try:
                    sock.close()
                except:
                    pass
    
    def get_stats(self):
        """Obtiene estadísticas de esta terminal"""
        total = self.conexiones_exitosas + self.conexiones_fallidas
        if total > 0:
            tasa_exito = (self.conexiones_exitosas / total) * 100
            latencia_prom = self.latencia_total / self.conexiones_exitosas if self.conexiones_exitosas > 0 else 0
        else:
            tasa_exito = 0
            latencia_prom = 0
        
        return {
            "maquina": self.maquina,
            "fallas": self.fallas_enviadas,
            "exitosas": self.conexiones_exitosas,
            "fallidas": self.conexiones_fallidas,
            "tasa_exito": tasa_exito,
            "latencia": latencia_prom
        }

class SimuladorCarga:
    """Controlador principal del simulador"""
    
    def __init__(self, num_terminals=10, fallas_por_minuto=60, host="localhost", port=5000):
        self.num_terminals = min(num_terminals, 200)  # Límite de 200 máquinas
        self.fallas_por_minuto = fallas_por_minuto
        self.fallas_por_segundo = fallas_por_minuto / 60.0
        self.host = host
        self.port = port
        self.running = False
        self.paused = False
        self.stop_event = threading.Event()
        
        # Terminales (máquinas)
        self.terminals = []
        for i in range(1, self.num_terminals + 1):
            self.terminals.append(TerminalAndon(i, host, port))
        
        # Estadísticas
        self.stats = {
            "total_fallas": 0,
            "exitosas": 0,
            "fallidas": 0,
            "fallas_por_boton": defaultdict(int),  # Contar por botón
            "fallas_por_maquina": defaultdict(int),
            "latencias": [],
            "inicio": None,
            "ultima_falla": None
        }
        
        # Lock para estadísticas (thread-safe)
        self.stats_lock = threading.Lock()
        
        self.main_thread = None
        
        print(f"\n{'='*50}")
        print(f"🚀 SIMULADOR DE CARGA ANDON")
        print(f"{'='*50}")
        print(f"📊 Máquinas: {len(self.terminals)}")
        print(f"⚡ Objetivo: {fallas_por_minuto} fallas/minuto")
        print(f"📈 Intervalo promedio: {(60.0/fallas_por_minuto)*1000:.1f}ms")
        print(f"🌐 Servidor: {host}:{port}")
        print(f"📡 Formato: maquina|BotonX (X=1-5)")
        print(f"{'='*50}\n")
    
    def generar_intervalo(self):
        """Genera intervalo con distribución exponencial"""
        if self.fallas_por_segundo <= 0:
            return 1.0
        return random.expovariate(self.fallas_por_segundo)
    
    def _worker(self):
        """Hilo único que programa los envíos"""
        fallas_en_este_minuto = 0
        ultimo_reporte = time.time()
        
        while not self.stop_event.is_set() and self.running:
            if not self.paused:
                # 1. Calcular intervalo
                intervalo = self.generar_intervalo()
                
                # 2. Esperar (permitir detención)
                if self.stop_event.wait(intervalo):
                    break
                
                # 3. Seleccionar terminal aleatoria
                terminal = random.choice(self.terminals)
                
                # 4. Enviar falla (botón aleatorio 1-5)
                exito, latencia, boton = terminal.enviar_falla()
                
                # 5. Actualizar estadísticas (thread-safe)
                with self.stats_lock:
                    self.stats["total_fallas"] += 1
                    fallas_en_este_minuto += 1
                    
                    if exito:
                        self.stats["exitosas"] += 1
                        self.stats["fallas_por_boton"][f"Botón{boton}"] += 1
                        self.stats["fallas_por_maquina"][terminal.maquina] += 1
                        self.stats["latencias"].append(latencia)
                        if len(self.stats["latencias"]) > 100:
                            self.stats["latencias"].pop(0)
                    else:
                        self.stats["fallidas"] += 1
                    
                    self.stats["ultima_falla"] = time.time()
                
                # Reporte cada minuto
                ahora = time.time()
                if ahora - ultimo_reporte >= 60:
                    with self.stats_lock:
                        tiempo_transcurrido = ahora - self.stats["inicio"]
                        tasa_real = (self.stats["total_fallas"] / tiempo_transcurrido) * 60 if tiempo_transcurrido > 0 else 0
                        
                        print(f"\n📊 [MINUTO] Fallas en último minuto: {fallas_en_este_minuto} (objetivo: {self.fallas_por_minuto})")
                        print(f"   Total acumulado: {self.stats['total_fallas']} | Tasa real: {tasa_real:.1f}/min")
                        if self.stats["latencias"]:
                            lat_prom = sum(self.stats["latencias"][-10:]) / min(10, len(self.stats["latencias"]))
                            print(f"   Latencia promedio (últimas): {lat_prom:.1f}ms")
                        
                        # Mostrar distribución de botones
                        if self.stats["fallas_por_boton"]:
                            print(f"   Distribución por botón:")
                            for boton, count in sorted(self.stats["fallas_por_boton"].items()):
                                print(f"      {boton}: {count}")
                    
                    fallas_en_este_minuto = 0
                    ultimo_reporte = ahora
            else:
                # Si está pausado, esperar sin consumir CPU
                if self.stop_event.wait(0.1):
                    break
    
    def verificar_conexion(self):
        """Verifica la conexión con el servidor sin afectar estadísticas"""
        if not self.terminals:
            return False
        
        print("🔍 Verificando conexión con el servidor Andon...")
        terminal_test = self.terminals[0]
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            sock.connect((self.host, self.port))
            sock.close()
            print("✅ Conexión con servidor Andon exitosa")
            return True
        except Exception as e:
            print(f"⚠️ No se pudo conectar con el servidor Andon: {e}")
            print("   Verifica que:")
            print("   1. Andon esté corriendo")
            print(f"   2. La IP {self.host} y puerto {self.port} sean correctos")
            print("   3. No haya firewall bloqueando la conexión")
            return False
    
    def start(self):
        """Inicia el simulador"""
        if not self.terminals:
            print("❌ No hay terminales para simular")
            return False
        
        # Verificar conexión
        if not self.verificar_conexion():
            response = input("¿Continuar de todas formas? (s/n): ")
            if response.lower() != 's':
                return False
        
        # Inicializar estadísticas
        self.stats["inicio"] = time.time()
        self.running = True
        self.stop_event.clear()
        
        # Iniciar worker
        self.main_thread = threading.Thread(target=self._worker, daemon=True)
        self.main_thread.start()
        
        return True
    
    def stop(self):
        """Detiene el simulador"""
        print("🛑 Deteniendo simulador...")
        self.running = False
        self.stop_event.set()
        
        if self.main_thread and self.main_thread.is_alive():
            self.main_thread.join(timeout=3.0)
        
        # Mostrar resumen final
        stats = self.get_resumen()
        print(f"\n📊 RESUMEN FINAL:")
        print(f"   Total fallas: {stats['total_fallas']}")
        print(f"   Exitosas: {stats['exitosas']} | Fallidas: {stats['fallidas']}")
        print(f"   Tasa real: {stats['tasa_real']:.1f}/min (objetivo: {stats['tasa_objetivo']})")
        print(f"   Distribución por botón:")
        for boton, count in sorted(stats['fallas_por_boton'].items()):
            print(f"      {boton}: {count}")
        print("✅ Simulador detenido")
    
    def get_resumen(self):
        """Obtiene resumen de estadísticas"""
        with self.stats_lock:
            ahora = time.time()
            duracion = ahora - self.stats["inicio"] if self.stats["inicio"] else 0
            
            # Calcular tasa real
            if duracion > 0:
                tasa_real = (self.stats["total_fallas"] / duracion) * 60
            else:
                tasa_real = 0
            
            # Calcular latencias
            if self.stats["latencias"]:
                lat_prom = sum(self.stats["latencias"]) / len(self.stats["latencias"])
                lat_min = min(self.stats["latencias"])
                lat_max = max(self.stats["latencias"])
            else:
                lat_prom = lat_min = lat_max = 0
            
            # Tasa de éxito
            if self.stats["total_fallas"] > 0:
                tasa_exito = (self.stats["exitosas"] / self.stats["total_fallas"]) * 100
            else:
                tasa_exito = 0
            
            # Estadísticas por máquina
            maquinas_stats = []
            for terminal in self.terminals[:10]:
                maquinas_stats.append(terminal.get_stats())
            maquinas_stats.sort(key=lambda x: x["fallas"], reverse=True)
            
            return {
                "total_fallas": self.stats["total_fallas"],
                "exitosas": self.stats["exitosas"],
                "fallidas": self.stats["fallidas"],
                "tasa_exito": tasa_exito,
                "tasa_real": tasa_real,
                "tasa_objetivo": self.fallas_por_minuto,
                "latencia_prom": lat_prom,
                "latencia_min": lat_min,
                "latencia_max": lat_max,
                "fallas_por_boton": dict(self.stats["fallas_por_boton"]),
                "fallas_por_maquina": dict(self.stats["fallas_por_maquina"]),
                "maquinas_top": maquinas_stats,
                "tiempo": duracion
            }

class InterfazSimulador:
    """Interfaz gráfica del simulador"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Simulador de Carga - Sistema Andon")
        self.root.geometry("1000x750")
        self.root.configure(bg=COLORES["fondo"])
        
        self.simulador = None
        self.running = False
        self.update_job = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz gráfica"""
        # Título
        tk.Label(self.root, text="🚀 SIMULADOR DE CARGA ANDON", 
                bg=COLORES["fondo"], fg=COLORES["texto"], 
                font=("Segoe UI", 20, "bold")).pack(pady=20)
        
        # Frame de configuración
        config_frame = tk.Frame(self.root, bg=COLORES["card"], padx=20, pady=20)
        config_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # IP y Puerto
        ip_frame = tk.Frame(config_frame, bg=COLORES["card"])
        ip_frame.pack(fill="x", pady=5)
        
        tk.Label(ip_frame, text="Servidor IP:", bg=COLORES["card"], fg=COLORES["texto"], 
                font=("Segoe UI", 10)).pack(side="left", padx=(0, 10))
        
        self.ip_var = tk.StringVar(value="localhost")
        tk.Entry(ip_frame, textvariable=self.ip_var, bg="#0f3460", fg=COLORES["texto"],
                font=("Segoe UI", 10), width=15).pack(side="left", padx=(0, 20))
        
        tk.Label(ip_frame, text="Puerto:", bg=COLORES["card"], fg=COLORES["texto"], 
                font=("Segoe UI", 10)).pack(side="left", padx=(0, 10))
        
        self.port_var = tk.StringVar(value="5000")
        tk.Entry(ip_frame, textvariable=self.port_var, bg="#0f3460", fg=COLORES["texto"],
                font=("Segoe UI", 10), width=8).pack(side="left")
        
        # Número de máquinas y frecuencia
        params_frame = tk.Frame(config_frame, bg=COLORES["card"])
        params_frame.pack(fill="x", pady=5)
        
        tk.Label(params_frame, text="Máquinas:", bg=COLORES["card"], fg=COLORES["texto"], 
                font=("Segoe UI", 10)).pack(side="left", padx=(0, 10))
        
        self.maquinas_var = tk.StringVar(value="10")
        tk.Spinbox(params_frame, from_=1, to=200, textvariable=self.maquinas_var,
                  bg="#0f3460", fg=COLORES["texto"], font=("Segoe UI", 10), width=8).pack(side="left", padx=(0, 20))
        
        tk.Label(params_frame, text="Fallas/min:", bg=COLORES["card"], fg=COLORES["texto"], 
                font=("Segoe UI", 10)).pack(side="left", padx=(0, 10))
        
        self.frecuencia_var = tk.StringVar(value="60")
        tk.Spinbox(params_frame, from_=1, to=600, textvariable=self.frecuencia_var,
                  bg="#0f3460", fg=COLORES["texto"], font=("Segoe UI", 10), width=8).pack(side="left")
        
        # Botones de control
        btn_frame = tk.Frame(config_frame, bg=COLORES["card"])
        btn_frame.pack(fill="x", pady=(15, 0))
        
        self.btn_iniciar = tk.Button(btn_frame, text="▶ INICIAR", 
                                     bg=COLORES["exito"], fg=COLORES["texto"], 
                                     font=("Segoe UI", 12, "bold"),
                                     padx=30, pady=10, cursor="hand2", command=self.iniciar_simulacion)
        self.btn_iniciar.pack(side="left", padx=5)
        
        self.btn_detener = tk.Button(btn_frame, text="⏹️ DETENER", 
                                     bg=COLORES["danger"], fg=COLORES["texto"], 
                                     font=("Segoe UI", 12, "bold"),
                                     padx=30, pady=10, cursor="hand2", state="disabled", 
                                     command=self.detener_simulacion)
        self.btn_detener.pack(side="left", padx=5)
        
        self.btn_pausa = tk.Button(btn_frame, text="⏸️ PAUSAR", 
                                   bg=COLORES["warning"], fg="black", 
                                   font=("Segoe UI", 12, "bold"),
                                   padx=30, pady=10, cursor="hand2", state="disabled",
                                   command=self.pausar_simulacion)
        self.btn_pausa.pack(side="left", padx=5)
        
        # Panel de estadísticas
        stats_frame = tk.Frame(self.root, bg=COLORES["fondo"])
        stats_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Frame superior con métricas principales
        top_stats = tk.Frame(stats_frame, bg=COLORES["card"])
        top_stats.pack(fill="x", pady=(0, 10))
        
        self.stats_labels = {}
        metricas = [
            ("Total", "0", "accento"),
            ("Exitosas", "0", "exito"),
            ("Fallidas", "0", "danger"),
            ("Tasa Éxito", "0%", "exito"),
            ("Tasa Real", "0/min", "warning"),
            ("Latencia", "0ms", "texto"),
        ]
        
        metrics_container = tk.Frame(top_stats, bg=COLORES["card"])
        metrics_container.pack(padx=15, pady=15)
        
        for i, (label, valor, color) in enumerate(metricas):
            frame = tk.Frame(metrics_container, bg="#0f3460", relief="flat", bd=1)
            frame.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
            
            tk.Label(frame, text=label, bg="#0f3460", fg=COLORES["texto"],
                    font=("Segoe UI", 10)).pack(pady=(5, 0))
            
            self.stats_labels[label] = tk.Label(frame, text=valor, bg="#0f3460", fg=COLORES[color],
                                                font=("Segoe UI", 14, "bold"))
            self.stats_labels[label].pack(pady=(0, 5))
        
        # Notebook para tabs
        notebook = ttk.Notebook(stats_frame)
        notebook.pack(fill="both", expand=True)
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook", background=COLORES["fondo"])
        style.configure("TNotebook.Tab", background=COLORES["card"], foreground=COLORES["texto"])
        style.map("TNotebook.Tab", background=[("selected", COLORES["accento"])])
        
        # Tab 1: Fallas por botón
        self.tab_botones = tk.Frame(notebook, bg=COLORES["card"])
        notebook.add(self.tab_botones, text="🔘 Por Botón")
        
        tk.Label(self.tab_botones, text="FALLAS POR BOTÓN", bg=COLORES["card"], fg=COLORES["texto"],
                font=("Segoe UI", 12, "bold")).pack(pady=10)
        
        self.botones_container = tk.Frame(self.tab_botones, bg=COLORES["card"])
        self.botones_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.barras_botones = {}
        colores_botones = ["#e94560", "#4CAF50", "#FFC107", "#2196F3", "#9C27B0"]
        
        for i in range(1, 6):
            boton = f"Botón{i}"
            frame = tk.Frame(self.botones_container, bg="#0f3460")
            frame.pack(fill="x", pady=3)
            
            tk.Label(frame, text=boton, bg="#0f3460", fg=COLORES["texto"],
                    font=("Segoe UI", 10), width=10, anchor="w").pack(side="left", padx=10)
            
            count_label = tk.Label(frame, text="0", bg="#0f3460", fg=colores_botones[i-1],
                                  font=("Segoe UI", 10, "bold"), width=6)
            count_label.pack(side="left", padx=5)
            
            barra_frame = tk.Frame(frame, bg=COLORES["fondo"], height=20, width=300)
            barra_frame.pack(side="left", padx=5)
            barra_frame.pack_propagate(False)
            
            barra = tk.Frame(barra_frame, bg=colores_botones[i-1], height=20, width=0)
            barra.pack(side="left")
            
            self.barras_botones[boton] = {
                "count": count_label,
                "barra": barra,
                "frame": barra_frame
            }
        
        # Tab 2: Máquinas activas
        self.tab_maquinas = tk.Frame(notebook, bg=COLORES["card"])
        notebook.add(self.tab_maquinas, text="⚙️ Máquinas")
        
        tk.Label(self.tab_maquinas, text="TOP 10 MÁQUINAS MÁS ACTIVAS", 
                bg=COLORES["card"], fg=COLORES["texto"],
                font=("Segoe UI", 12, "bold")).pack(pady=10)
        
        self.maquinas_container = tk.Frame(self.tab_maquinas, bg=COLORES["card"])
        self.maquinas_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Scroll para máquinas
        canvas = tk.Canvas(self.maquinas_container, bg=COLORES["card"], highlightthickness=0)
        scrollbar = tk.Scrollbar(self.maquinas_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORES["card"])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        self.maquinas_list_frame = scrollable_frame
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Estado
        self.estado_label = tk.Label(self.root, text="⏸️ SIMULADOR DETENIDO", 
                                     bg=COLORES["fondo"], fg=COLORES["warning"],
                                     font=("Segoe UI", 10, "bold"))
        self.estado_label.pack(pady=5)
        
        # Info de formato
        info_frame = tk.Frame(self.root, bg=COLORES["fondo"])
        info_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        tk.Label(info_frame, text="📡 Formato enviado: maquina|BotonX (X=1-5)", 
                bg=COLORES["fondo"], fg=COLORES["texto_secundario"] if "texto_secundario" in COLORES else "#b0b0b0",
                font=("Segoe UI", 9)).pack()
        tk.Label(info_frame, text="💡 El mapeo a tipos de falla se realiza en la configuración del servidor Andon", 
                bg=COLORES["fondo"], fg=COLORES["texto_secundario"] if "texto_secundario" in COLORES else "#b0b0b0",
                font=("Segoe UI", 9, "italic")).pack()
    
    def iniciar_simulacion(self):
        """Inicia la simulación"""
        try:
            num_maquinas = int(self.maquinas_var.get())
            fallas_min = int(self.frecuencia_var.get())
            host = self.ip_var.get()
            port = int(self.port_var.get())
            
            if fallas_min <= 0:
                messagebox.showerror("Error", "Las fallas por minuto deben ser mayores a 0")
                return
            
            if num_maquinas > 200:
                messagebox.showwarning("Límite", "Andon soporta máximo 200 máquinas. Usando 200.")
                num_maquinas = 200
            
            # Crear y iniciar simulador
            self.simulador = SimuladorCarga(num_maquinas, fallas_min, host, port)
            if not self.simulador.start():
                return
            
            # Actualizar UI
            self.running = True
            self.btn_iniciar.config(state="disabled")
            self.btn_detener.config(state="normal")
            self.btn_pausa.config(state="normal", text="⏸️ PAUSAR")
            self.estado_label.config(text="▶️ SIMULACIÓN ACTIVA", fg=COLORES["exito"])
            
            # Iniciar actualización de stats
            self.actualizar_stats()
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo iniciar: {str(e)}")
    
    def detener_simulacion(self):
        """Detiene la simulación"""
        if self.simulador:
            self.simulador.stop()
        
        self.running = False
        self.btn_iniciar.config(state="normal")
        self.btn_detener.config(state="disabled")
        self.btn_pausa.config(state="disabled")
        self.estado_label.config(text="⏸️ SIMULADOR DETENIDO", fg=COLORES["warning"])
        
        # Cancelar actualizaciones pendientes
        if self.update_job:
            self.root.after_cancel(self.update_job)
            self.update_job = None
    
    def pausar_simulacion(self):
        """Pausa/reanuda la simulación"""
        if not self.simulador:
            return
        
        self.simulador.paused = not self.simulador.paused
        
        if self.simulador.paused:
            self.btn_pausa.config(text="▶️ REANUDAR", bg=COLORES["exito"])
            self.estado_label.config(text="⏸️ SIMULACIÓN PAUSADA", fg=COLORES["warning"])
        else:
            self.btn_pausa.config(text="⏸️ PAUSAR", bg=COLORES["warning"])
            self.estado_label.config(text="▶️ SIMULACIÓN ACTIVA", fg=COLORES["exito"])
    
    def actualizar_stats(self):
        """Actualiza las estadísticas en la interfaz"""
        if not self.simulador or not self.running:
            return
        
        stats = self.simulador.get_resumen()
        
        # Actualizar métricas principales
        self.stats_labels["Total"].config(text=str(stats["total_fallas"]))
        self.stats_labels["Exitosas"].config(text=str(stats["exitosas"]))
        self.stats_labels["Fallidas"].config(text=str(stats["fallidas"]))
        self.stats_labels["Tasa Éxito"].config(text=f"{stats['tasa_exito']:.1f}%")
        self.stats_labels["Tasa Real"].config(text=f"{stats['tasa_real']:.1f}/min")
        self.stats_labels["Latencia"].config(text=f"{stats['latencia_prom']:.1f}ms")
        
        # Actualizar barras por botón
        if stats["fallas_por_boton"]:
            max_count = max(stats["fallas_por_boton"].values()) if stats["fallas_por_boton"] else 1
            
            for boton, data in self.barras_botones.items():
                count = stats["fallas_por_boton"].get(boton, 0)
                data["count"].config(text=str(count))
                
                if max_count > 0:
                    ancho = int((count / max_count) * 300)
                    data["barra"].config(width=ancho)
        
        # Actualizar lista de máquinas
        for widget in self.maquinas_list_frame.winfo_children():
            widget.destroy()
        
        for i, m_stats in enumerate(stats["maquinas_top"][:10]):
            frame = tk.Frame(self.maquinas_list_frame, bg="#0f3460")
            frame.pack(fill="x", pady=2)
            
            texto = (f"Máq {m_stats['maquina']}: {m_stats['fallas']} fallas "
                    f"| {m_stats['tasa_exito']:.0f}% éxito "
                    f"| {m_stats['latencia']:.1f}ms")
            
            tk.Label(frame, text=texto, bg="#0f3460", fg=COLORES["texto"],
                    font=("Segoe UI", 10)).pack(padx=10, pady=5)
        
        # Programar próxima actualización
        self.update_job = self.root.after(500, self.actualizar_stats)
    
    def run(self):
        """Ejecuta la interfaz"""
        try:
            self.root.mainloop()
        finally:
            if self.simulador and self.running:
                self.simulador.stop()

def main_consola():
    """Versión de línea de comandos"""
    parser = argparse.ArgumentParser(description="Simulador de Carga Andon")
    parser.add_argument("--maquinas", type=int, default=10, help="Número de máquinas (1-200)")
    parser.add_argument("--rate", type=int, default=60, help="Fallas por minuto")
    parser.add_argument("--host", type=str, default="localhost", help="IP del servidor Andon")
    parser.add_argument("--port", type=int, default=5000, help="Puerto")
    parser.add_argument("--duration", type=int, default=0, help="Duración en segundos")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🚀 SIMULADOR DE CARGA ANDON (MODO CONSOLA)")
    print("=" * 60)
    print(f"📡 Formato: maquina|BotonX (X=1-5)")
    print("=" * 60)
    
    simulador = SimuladorCarga(args.maquinas, args.rate, args.host, args.port)
    
    def signal_handler(sig, frame):
        print("\n🛑 Deteniendo simulación...")
        simulador.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    if not simulador.start():
        return
    
    if args.duration > 0:
        print(f"⏳ Simulando por {args.duration} segundos...")
        
        try:
            time.sleep(args.duration)
        except KeyboardInterrupt:
            pass
        finally:
            simulador.stop()
            
            stats = simulador.get_resumen()
            print("\n" + "=" * 60)
            print("📊 RESUMEN FINAL")
            print("=" * 60)
            print(f"Total fallas: {stats['total_fallas']}")
            print(f"Exitosas: {stats['exitosas']} | Fallidas: {stats['fallidas']}")
            print(f"Tasa éxito: {stats['tasa_exito']:.1f}%")
            print(f"Tasa real: {stats['tasa_real']:.2f} fallas/min (obj: {stats['tasa_objetivo']})")
            print(f"Latencia promedio: {stats['latencia_prom']:.2f} ms")
            print(f"Distribución por botón:")
            for boton, count in sorted(stats['fallas_por_boton'].items()):
                print(f"   {boton}: {count}")
            print("=" * 60)
    else:
        print("⏳ Simulación en ejecución. Presiona Ctrl+C para detener.")
        print("-" * 60)
        
        try:
            while True:
                time.sleep(10)
                stats = simulador.get_resumen()
                print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                      f"Total: {stats['total_fallas']} | "
                      f"Tasa: {stats['tasa_real']:.1f}/min | "
                      f"Lat: {stats['latencia_prom']:.1f}ms | "
                      f"Éxito: {stats['tasa_exito']:.1f}%")
        except KeyboardInterrupt:
            simulador.stop()
            print("\n✅ Simulación detenida")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        main_consola()
    else:
        app = InterfazSimulador()
        app.run()