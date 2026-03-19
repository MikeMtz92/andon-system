# src/views/esp32_view.py

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import socket
from src.utils.widgets import ModernButton, ModernEntry
import logging

logger = logging.getLogger(__name__)

class ESP32View:
    """Ventana para generar código para ESP32"""
    
    def __init__(self, parent, controller, theme_service, falla_controller):
        self.parent = parent
        self.controller = controller
        self.theme = theme_service
        self.falla_controller = falla_controller
        
        self.ventana = tk.Toplevel(parent)
        self.ventana.title("Generar Código ESP32")
        self.ventana.geometry("600x700")
        self.ventana.configure(bg=self.theme.colores["fondo"])
        self.ventana.resizable(False, False)
        self.ventana.transient(parent)
        self.ventana.grab_set()
        
        # Centrar ventana
        self.ventana.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (600 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (700 // 2)
        self.ventana.geometry(f"+{x}+{y}")
        
        # Variables
        self.esp32_numero = tk.StringVar(value="1")
        self.esp32_server_ip = tk.StringVar(value="192.168.1.10")
        self.pin_assignments = {}
        self.tipos_falla = []
        
        self._cargar_tipos()
        self._setup_ui()
        
    def _cargar_tipos(self):
        """Carga los tipos de falla disponibles"""
        tipos_data = self.falla_controller.falla_model.cargar_tipos_falla()
        self.tipos_falla = [t["nombre"] for t in tipos_data]
        
        # Limitar según licencia
        max_tipos = self.controller.licencia_controller.max_tipos_falla
        if len(self.tipos_falla) > max_tipos:
            self.tipos_falla = self.tipos_falla[:max_tipos]
        
    def _setup_ui(self):
        """Configura la interfaz de usuario"""
        # Título
        tk.Label(self.ventana,
                text="⚙️ Generar Código para ESP32",
                bg=self.theme.colores["fondo"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 18, "bold")).pack(pady=20)
        
        # Frame principal con scroll
        main_frame = tk.Frame(self.ventana, bg=self.theme.colores["fondo"])
        main_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        canvas = tk.Canvas(main_frame, bg=self.theme.colores["fondo"], highlightthickness=0, height=500)
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.theme.colores["fondo"])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # ===== NÚMERO DE MÁQUINA =====
        self._crear_seccion_maquina(scrollable_frame)
        
        # ===== PINES DEL ESP32 =====
        self._crear_seccion_pines(scrollable_frame)
        
        # ===== ASIGNACIÓN DE BOTONES =====
        self._crear_seccion_botones(scrollable_frame)
        
        # ===== IP DEL SERVIDOR =====
        self._crear_seccion_ip(scrollable_frame)
        
        # ===== VISTA PREVIA DEL CÓDIGO =====
        self._crear_seccion_codigo(scrollable_frame)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # ===== BOTONES DE ACCIÓN =====
        self._crear_botones_accion()
        
    def _crear_seccion_maquina(self, parent):
        """Crea la sección de número de máquina"""
        card = tk.Frame(parent, bg=self.theme.colores["card"], relief="flat", bd=1)
        card.pack(fill="x", pady=(0, 15))
        
        tk.Label(card,
                text="🔢 Número de Máquina",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15, pady=(15, 10))
        
        maquina_frame = tk.Frame(card, bg=self.theme.colores["card"])
        maquina_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        tk.Label(maquina_frame,
                text="Máquina:",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto_secundario"],
                font=("Segoe UI", 10)).pack(side="left", padx=(0, 10))
        
        spinbox = tk.Spinbox(maquina_frame,
                           from_=1, to=99,
                           textvariable=self.esp32_numero,
                           width=5,
                           bg=self.theme.colores.get("superficie3", "#2d3047"),
                           fg=self.theme.colores["texto"],
                           font=("Segoe UI", 10),
                           relief="flat")
        spinbox.pack(side="left", padx=(0, 10))
        
        # Mostrar IP sugerida
        self.ip_sugerida_label = tk.Label(maquina_frame,
                                         text="",
                                         bg=self.theme.colores["card"],
                                         fg=self.theme.colores["texto_secundario"],
                                         font=("Segoe UI", 10))
        self.ip_sugerida_label.pack(side="left")
        self._actualizar_ip_sugerida()
        
        # Actualizar IP cuando cambie el número
        spinbox.config(command=self._actualizar_ip_sugerida)
        self.esp32_numero.trace_add("write", lambda *args: self._actualizar_ip_sugerida())
        
    def _crear_seccion_pines(self, parent):
        """Crea la sección de información de pines"""
        card = tk.Frame(parent, bg=self.theme.colores["card"], relief="flat", bd=1)
        card.pack(fill="x", pady=(0, 15))
        
        tk.Label(card,
                text="🔌 Pines del ESP32",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15, pady=(15, 10))
        
        # Pines W5500 (obligatorios)
        w5500_frame = tk.Frame(card, bg=self.theme.colores["card"])
        w5500_frame.pack(fill="x", padx=15, pady=5)
        
        tk.Label(w5500_frame,
                text="🔌 W5500 (Obligatorios):",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["danger"],
                font=("Segoe UI", 10, "bold")).pack(anchor="w")
        
        pins_frame = tk.Frame(w5500_frame, bg=self.theme.colores["card"])
        pins_frame.pack(fill="x", pady=5)
        
        pines_w5500 = ["D23", "D19", "D18", "D5", "D4"]
        for pin in pines_w5500:
            tk.Label(pins_frame,
                    text=pin,
                    bg=self.theme.colores["danger"],
                    fg=self.theme.colores["texto"],
                    font=("Segoe UI", 8),
                    width=5,
                    relief="flat").pack(side="left", padx=2)
        
        tk.Label(card,
                text="Los pines W5500 son fijos y no pueden reasignarse",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto_secundario"],
                font=("Segoe UI", 9, "italic")).pack(anchor="w", padx=15, pady=(0, 15))
        
    def _crear_seccion_botones(self, parent):
        """Crea la sección de asignación de botones"""
        card = tk.Frame(parent, bg=self.theme.colores["card"], relief="flat", bd=1)
        card.pack(fill="x", pady=(0, 15))
        
        tk.Label(card,
                text="🎚️ Asignación de Botones",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15, pady=(15, 10))
        
        # Lista de pines disponibles para botones
        pines_disponibles = ["D14", "D27", "D26", "D25", "D33", "D32", "D15", "D2", "D13", "D12", "D21", "D22"]
        
        botones_frame = tk.Frame(card, bg=self.theme.colores["card"])
        botones_frame.pack(fill="x", padx=15, pady=5)
        
        for i, tipo in enumerate(self.tipos_falla):
            row = tk.Frame(botones_frame, bg=self.theme.colores["card"])
            row.pack(fill="x", pady=2)
            
            # Nombre del tipo
            tk.Label(row,
                    text=f"{tipo}:",
                    bg=self.theme.colores["card"],
                    fg=self.theme.colores["texto"],
                    font=("Segoe UI", 9),
                    width=15,
                    anchor="w").pack(side="left", padx=(0, 10))
            
            # Selector de pin
            pin_var = tk.StringVar(value=pines_disponibles[i] if i < len(pines_disponibles) else "D32")
            combo = ttk.Combobox(row,
                                textvariable=pin_var,
                                values=pines_disponibles,
                                width=8,
                                state="readonly")
            combo.pack(side="left", padx=5)
            
            # Indicador de disponibilidad
            status_frame = tk.Frame(row, bg=self.theme.colores["card"])
            status_frame.pack(side="left", padx=10)
            
            status_label = tk.Label(status_frame,
                                   text="●",
                                   fg="#4CAF50",
                                   bg=self.theme.colores["card"],
                                   font=("Arial", 10))
            status_label.pack(side="left")
            
            status_text = tk.Label(status_frame,
                                  text="Libre",
                                  bg=self.theme.colores["card"],
                                  fg=self.theme.colores["texto_secundario"],
                                  font=("Segoe UI", 8))
            status_text.pack(side="left", padx=5)
            
            # Guardar referencia
            self.pin_assignments[tipo] = {
                "var": pin_var,
                "status": status_label,
                "status_text": status_text,
                "combobox": combo
            }
            
            # Función para actualizar estado cuando cambie la selección
            def make_update(t):
                return lambda *args: self._actualizar_estado_pin(t)
            
            combo.bind("<<ComboboxSelected>>", make_update(tipo))
        
        # Actualizar estados iniciales
        for tipo in self.tipos_falla:
            self._actualizar_estado_pin(tipo)
            
    def _actualizar_estado_pin(self, tipo):
        """Actualiza el estado de un pin (libre/ocupado)"""
        if tipo not in self.pin_assignments:
            return
        
        pin = self.pin_assignments[tipo]["var"].get()
        
        # Verificar si el pin está ocupado por otro botón
        ocupado = False
        for otro_tipo, data in self.pin_assignments.items():
            if otro_tipo != tipo and data["var"].get() == pin:
                ocupado = True
                break
        
        color = "#FF5252" if ocupado else "#4CAF50"
        texto = "Ocupado" if ocupado else "Libre"
        
        self.pin_assignments[tipo]["status"].config(fg=color)
        self.pin_assignments[tipo]["status_text"].config(text=texto)
        
    def _crear_seccion_ip(self, parent):
        """Crea la sección de IP del servidor"""
        card = tk.Frame(parent, bg=self.theme.colores["card"], relief="flat", bd=1)
        card.pack(fill="x", pady=(0, 15))
        
        tk.Label(card,
                text="🌐 IP del Servidor",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15, pady=(15, 10))
        
        ip_frame = tk.Frame(card, bg=self.theme.colores["card"])
        ip_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        entry = tk.Entry(ip_frame,
                        textvariable=self.esp32_server_ip,
                        width=20,
                        bg=self.theme.colores.get("superficie3", "#2d3047"),
                        fg=self.theme.colores["texto"],
                        font=("Segoe UI", 10),
                        relief="flat")
        entry.pack(side="left", padx=(0, 10))
        
        tk.Button(ip_frame,
                 text="Mi IP Actual",
                 bg=self.theme.colores["card"],
                 fg=self.theme.colores["texto"],
                 font=("Segoe UI", 8),
                 relief="flat",
                 padx=10,
                 cursor="hand2",
                 command=self._obtener_ip_actual).pack(side="left")
        
    def _crear_seccion_codigo(self, parent):
        """Crea la sección de vista previa del código"""
        card = tk.Frame(parent, bg=self.theme.colores["card"], relief="flat", bd=1)
        card.pack(fill="x", pady=(0, 15))
        
        tk.Label(card,
                text="📝 Vista Previa del Código",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15, pady=(15, 10))
        
        self.code_preview = tk.Text(card,
                                   height=15,
                                   width=50,
                                   bg="#1e1e1e",
                                   fg="#d4d4d4",
                                   font=("Consolas", 9),
                                   relief="flat",
                                   wrap="none")
        self.code_preview.pack(fill="x", padx=15, pady=(0, 10))
        
        scroll_x = tk.Scrollbar(card, orient="horizontal", command=self.code_preview.xview)
        self.code_preview.configure(xscrollcommand=scroll_x.set)
        scroll_x.pack(fill="x", padx=15, pady=(0, 15))
        
        # Generar código inicial
        self._generar_codigo()
        
        # Actualizar cuando cambien los valores
        self.esp32_numero.trace_add("write", lambda *args: self._generar_codigo())
        self.esp32_server_ip.trace_add("write", lambda *args: self._generar_codigo())
        
        # Botón actualizar
        tk.Button(card,
                 text="🔄 Actualizar Vista Previa",
                 bg=self.theme.colores["card"],
                 fg=self.theme.colores["texto"],
                 font=("Segoe UI", 9),
                 relief="flat",
                 padx=10,
                 pady=3,
                 cursor="hand2",
                 command=self._generar_codigo).pack(pady=(0, 15))
        
    def _crear_botones_accion(self):
        """Crea los botones de acción"""
        btn_frame = tk.Frame(self.ventana, bg=self.theme.colores["fondo"])
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        tk.Button(btn_frame,
                 text="💾 Generar Archivo .ino",
                 bg=self.theme.colores["success"],
                 fg=self.theme.colores["texto"],
                 font=("Segoe UI", 11, "bold"),
                 relief="flat",
                 padx=20,
                 pady=10,
                 cursor="hand2",
                 command=self._guardar_codigo).pack(side="right", padx=5)
        
        tk.Button(btn_frame,
                 text="🚫 Cancelar",
                 bg=self.theme.colores["danger"],
                 fg=self.theme.colores["texto"],
                 font=("Segoe UI", 11),
                 relief="flat",
                 padx=20,
                 pady=10,
                 cursor="hand2",
                 command=self.ventana.destroy).pack(side="right", padx=5)
        
    def _actualizar_ip_sugerida(self):
        """Actualiza la IP sugerida basada en el número de máquina"""
        try:
            num = int(self.esp32_numero.get())
            ip_octet = 100 + num
            self.ip_sugerida_label.config(text=f"(IP sugerida: 192.168.1.{ip_octet})")
        except:
            self.ip_sugerida_label.config(text="")
            
    def _obtener_ip_actual(self):
        """Obtiene la IP local de la PC"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            self.esp32_server_ip.set(ip)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo obtener la IP:\n{str(e)}")
            
    def _generar_codigo(self):
        """Genera el código para ESP32"""
        try:
            num_maquina = int(self.esp32_numero.get())
            ip_octet = 100 + num_maquina
            mac_suffix = f"{num_maquina:02X}"
            
            # Recoger pines asignados
            pines = []
            for tipo in self.tipos_falla:
                if tipo in self.pin_assignments:
                    pin_str = self.pin_assignments[tipo]["var"].get()
                    pin_num = pin_str.replace("D", "")
                    pines.append(pin_num)
            
            # Generar código
            lineas = []
            lineas.append("#include <SPI.h>")
            lineas.append("#include <Ethernet.h>")
            lineas.append("")
            lineas.append(f"const int numeroMaquina = {num_maquina};")
            lineas.append(f"const int numBotones = {len(pines)};")
            lineas.append("")
            lineas.append(f"const int botones[] = {{{', '.join(pines)}}};")
            lineas.append("")
            lineas.append("#define PIN_CS  5")
            lineas.append("#define PIN_RST 4")
            lineas.append("")
            lineas.append(f"byte mac[] = {{ 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0x{mac_suffix} }};")
            lineas.append(f"IPAddress ip(192, 168, 1, {ip_octet});")
            
            ip_parts = self.esp32_server_ip.get().split('.')
            lineas.append(f"IPAddress serverIP({', '.join(ip_parts)});")
            
            lineas.append("const uint16_t serverPort = 5000;")
            lineas.append("")
            lineas.append("EthernetClient client;")
            lineas.append(f"bool estadoAnterior[numBotones] = {{false}};")
            lineas.append("")
            lineas.append("void setup() {")
            lineas.append("    Serial.begin(115200);")
            lineas.append("    Serial.println(\"Máquina \" + String(numeroMaquina));")
            lineas.append("")
            lineas.append("    Ethernet.init(PIN_CS);")
            lineas.append("    Ethernet.begin(mac, ip);")
            lineas.append("")
            lineas.append("    Serial.print(\"IP: \");")
            lineas.append("    Serial.println(Ethernet.localIP());")
            lineas.append("")
            lineas.append("    for (int i = 0; i < numBotones; i++) {")
            lineas.append("        pinMode(botones[i], INPUT_PULLUP);")
            lineas.append("        Serial.print(\"Botón \");")
            lineas.append("        Serial.print(i+1);")
            lineas.append("        Serial.print(\" en pin D\");")
            lineas.append("        Serial.println(botones[i]);")
            lineas.append("    }")
            lineas.append("}")
            lineas.append("")
            lineas.append("void loop() {")
            lineas.append("    for (int i = 0; i < numBotones; i++) {")
            lineas.append("        bool presionado = (digitalRead(botones[i]) == LOW);")
            lineas.append("        if (presionado && !estadoAnterior[i]) {")
            lineas.append("            enviarEvento(i+1);")
            lineas.append("        }")
            lineas.append("        estadoAnterior[i] = presionado;")
            lineas.append("    }")
            lineas.append("    delay(50);")
            lineas.append("}")
            lineas.append("")
            lineas.append("void enviarEvento(int numeroBoton) {")
            lineas.append("    Serial.print(\"Evento: Botón \");")
            lineas.append("    Serial.println(numeroBoton);")
            lineas.append("")
            lineas.append("    if (client.connect(serverIP, serverPort)) {")
            lineas.append("        String mensaje = String(numeroMaquina) + \"|Boton\" + String(numeroBoton) + \"\\n\";")
            lineas.append("        client.print(mensaje);")
            lineas.append("        client.stop();")
            lineas.append("        Serial.println(\"✓ Enviado\");")
            lineas.append("    } else {")
            lineas.append("        Serial.println(\"✗ Error conexión\");")
            lineas.append("    }")
            lineas.append("}")
            
            codigo = "\n".join(lineas)
            
            self.code_preview.delete(1.0, tk.END)
            self.code_preview.insert(1.0, codigo)
            
        except Exception as e:
            logger.error(f"Error generando código: {e}")
            self.code_preview.delete(1.0, tk.END)
            self.code_preview.insert(1.0, f"// Error generando código: {str(e)}")
            
    def _guardar_codigo(self):
        """Guarda el código en un archivo .ino"""
        num_maquina = self.esp32_numero.get()
        file_path = filedialog.asksaveasfilename(
            defaultextension=".ino",
            initialfile=f"andon_maquina_{num_maquina}.ino",
            filetypes=[("Arduino files", "*.ino"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            codigo = self.code_preview.get(1.0, tk.END)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(codigo)
            messagebox.showinfo("✅ Código Generado", f"Archivo guardado en:\n{file_path}")
            self.ventana.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar:\n{str(e)}")