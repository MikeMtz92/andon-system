# src/views/pendientes_view.py

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from src.utils.helpers import solo_hora
import logging

logger = logging.getLogger(__name__)

class PendientesView:
    """Ventana para visualizar y gestionar fallas pendientes"""
    
    def __init__(self, parent, controller, theme_service, falla_controller):
        self.parent = parent
        self.controller = controller
        self.theme = theme_service
        self.falla_controller = falla_controller
        
        # Obtener fallas pendientes
        self.pendientes = self.falla_controller.get_fallas_pendientes()
        
        if not self.pendientes:
            messagebox.showinfo("Información", "No hay fallas pendientes")
            return
        
        self.ventana = tk.Toplevel(parent)
        self.ventana.title("Fallas Pendientes")
        self.ventana.geometry("900x600")
        self.ventana.configure(bg=self.theme.colores["fondo"])
        self.ventana.transient(parent)
        self.ventana.grab_set()
        
        # Centrar ventana
        self.ventana.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (900 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (600 // 2)
        self.ventana.geometry(f"+{x}+{y}")
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Configura la interfaz de usuario"""
        # Header
        header = tk.Frame(self.ventana, bg=self.theme.colores["card"])
        header.pack(fill="x", padx=20, pady=20)
        
        tk.Label(header,
                text=f"📋 Fallas Pendientes ({len(self.pendientes)})",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=20, pady=10)
        
        # Tabla
        self._crear_tabla()
        
        # Botones de acción
        self._crear_botones()
        
    def _crear_tabla(self):
        """Crea la tabla de fallas pendientes"""
        tree_frame = tk.Frame(self.ventana, bg=self.theme.colores["fondo"])
        tree_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        columnas = ("#", "Máquina", "Tipo", "Inicio", "Fecha Pendiente", "Nota")
        
        self.tree = ttk.Treeview(tree_frame, columns=columnas, show="headings", height=15)
        
        # Configurar columnas
        anchos = [50, 80, 120, 150, 150, 250]
        for col, ancho in zip(columnas, anchos):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=ancho, anchor="center")
        
        self.tree.column("Nota", width=250, anchor="w")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Configurar colores
        self.tree.tag_configure("pendiente", 
                               background=self.theme.colores.get("pendiente", "#FFA500"))
        
        # Insertar datos
        for alerta in self.pendientes:
            self._insertar_fila(alerta)
        
        # Bind doble clic
        self.tree.bind("<Double-1>", self._on_doble_click)
        
    def _insertar_fila(self, alerta):
        """Inserta una fila en la tabla"""
        # Formatear fechas
        inicio = alerta.get("inicio", "")
        if inicio and len(inicio) > 10:
            inicio = inicio[11:16]
        
        fecha_pendiente = alerta.get("fecha_pendiente", "")
        if fecha_pendiente and len(fecha_pendiente) > 10:
            fecha_pendiente = fecha_pendiente[11:16]
        
        nota = alerta.get("nota_pendiente", "")
        if len(nota) > 50:
            nota = nota[:50] + "..."
        
        valores = (
            f"#{alerta.get('numero_falla', '?')}",
            alerta["maquina"],
            alerta["tipo"],
            inicio,
            fecha_pendiente,
            nota
        )
        
        self.tree.insert("", "end", values=valores, tags=("pendiente",), iid=str(id(alerta)))
        
    def _crear_botones(self):
        """Crea los botones de acción"""
        btn_frame = tk.Frame(self.ventana, bg=self.theme.colores["fondo"])
        btn_frame.pack(fill="x", padx=20, pady=20)
        
        tk.Button(btn_frame,
                 text="✅ Marcar Seleccionada como Resuelta",
                 bg=self.theme.colores["success"],
                 fg=self.theme.colores["texto"],
                 font=("Segoe UI", 11),
                 relief="flat",
                 padx=15,
                 pady=8,
                 cursor="hand2",
                 command=self._resolver_seleccionada).pack(side="left", padx=5)
        
        tk.Button(btn_frame,
                 text="📋 Ver Detalle",
                 bg=self.theme.colores["accento"],
                 fg=self.theme.colores["texto"],
                 font=("Segoe UI", 11),
                 relief="flat",
                 padx=15,
                 pady=8,
                 cursor="hand2",
                 command=self._ver_detalle).pack(side="left", padx=5)
        
        tk.Button(btn_frame,
                 text="❌ Cerrar",
                 bg=self.theme.colores["danger"],
                 fg=self.theme.colores["texto"],
                 font=("Segoe UI", 11),
                 relief="flat",
                 padx=15,
                 pady=8,
                 cursor="hand2",
                 command=self.ventana.destroy).pack(side="right", padx=5)
        
    def _on_doble_click(self, event):
        """Maneja doble clic en la tabla"""
        self._ver_detalle()
        
    def _obtener_falla_seleccionada(self):
        """Obtiene la falla seleccionada en la tabla"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Seleccionar", "Por favor selecciona una falla")
            return None
        
        item_id = selection[0]
        for alerta in self.pendientes:
            if str(id(alerta)) == item_id:
                return alerta
        return None
        
    def _ver_detalle(self):
        """Muestra el detalle de la falla seleccionada"""
        alerta = self._obtener_falla_seleccionada()
        if not alerta:
            return
        
        self._mostrar_detalle(alerta)
        
    def _mostrar_detalle(self, alerta):
        """Muestra ventana con detalle de la falla"""
        dialog = tk.Toplevel(self.ventana)
        dialog.title("Detalle de Falla Pendiente")
        dialog.geometry("500x400")
        dialog.configure(bg=self.theme.colores["fondo"])
        dialog.transient(self.ventana)
        dialog.grab_set()
        
        # Centrar
        dialog.update_idletasks()
        x = self.ventana.winfo_x() + (self.ventana.winfo_width() // 2) - (500 // 2)
        y = self.ventana.winfo_y() + (self.ventana.winfo_height() // 2) - (400 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Título
        tk.Label(dialog,
                text="📋 Detalle de Falla Pendiente",
                bg=self.theme.colores["fondo"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 16, "bold")).pack(pady=20)
        
        # Información
        info = tk.Frame(dialog, bg=self.theme.colores["card"])
        info.pack(fill="x", padx=20, pady=10)
        
        tk.Label(info,
                text=f"Máquina: {alerta['maquina']}",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=10, pady=5)
        
        tk.Label(info,
                text=f"Tipo: {alerta['tipo']}",
                bg=self.theme.colores["card"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 11)).pack(anchor="w", padx=10, pady=5)
        
        if alerta.get("fecha_pendiente"):
            tk.Label(info,
                    text=f"Fecha: {alerta['fecha_pendiente']}",
                    bg=self.theme.colores["card"],
                    fg=self.theme.colores["texto_secundario"],
                    font=("Segoe UI", 10)).pack(anchor="w", padx=10, pady=5)
        
        # Nota
        tk.Label(dialog,
                text="Nota:",
                bg=self.theme.colores["fondo"],
                fg=self.theme.colores["texto"],
                font=("Segoe UI", 11, "bold")).pack(pady=(20, 5))
        
        texto_nota = tk.Text(dialog,
                            height=8,
                            width=50,
                            bg=self.theme.colores.get("superficie3", "#2d3047"),
                            fg=self.theme.colores["texto"],
                            font=("Segoe UI", 10),
                            wrap="word")
        texto_nota.pack(padx=20, pady=5)
        texto_nota.insert("1.0", alerta.get("nota_pendiente", ""))
        texto_nota.config(state="disabled")
        
        # Botones
        btn_frame = tk.Frame(dialog, bg=self.theme.colores["fondo"])
        btn_frame.pack(pady=20)
        
        def resolver():
            dialog.destroy()
            self._resolver_falla(alerta)
        
        tk.Button(btn_frame,
                 text="✅ Marcar como Resuelta",
                 bg=self.theme.colores["success"],
                 fg=self.theme.colores["texto"],
                 font=("Segoe UI", 10, "bold"),
                 relief="flat",
                 padx=15,
                 pady=8,
                 cursor="hand2",
                 command=resolver).pack(side="left", padx=5)
        
        tk.Button(btn_frame,
                 text="❌ Cerrar",
                 bg=self.theme.colores["danger"],
                 fg=self.theme.colores["texto"],
                 font=("Segoe UI", 10),
                 relief="flat",
                 padx=15,
                 pady=8,
                 cursor="hand2",
                 command=dialog.destroy).pack(side="left", padx=5)
        
    def _resolver_seleccionada(self):
        """Resuelve la falla seleccionada"""
        alerta = self._obtener_falla_seleccionada()
        if alerta:
            self._resolver_falla(alerta)
            
    def _resolver_falla(self, alerta):
        """Resuelve una falla pendiente"""
        respuesta = messagebox.askyesno(
            "Confirmar",
            f"¿La falla de máquina {alerta['maquina']} - {alerta['tipo']} ha sido resuelta?"
        )
        
        if respuesta:
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if "proceso" not in alerta or not alerta["proceso"]:
                alerta["proceso"] = ahora
            
            alerta["fin"] = ahora
            alerta["estado"] = "resuelta"
            
            # Guardar en BD
            self.falla_controller.falla_model.guardar_falla_en_historial(alerta)
            self.falla_controller.falla_model.eliminar_falla_activa(alerta.get("numero_falla"))
            
            # Eliminar de la lista en memoria
            if alerta in self.falla_controller.fallas_activas:
                self.falla_controller.fallas_activas.remove(alerta)
            
            # Actualizar vistas
            if self.falla_controller.on_fallas_actualizadas:
                self.falla_controller.on_fallas_actualizadas()
            
            messagebox.showinfo("✅ Completado", "Falla resuelta y registrada")
            self.ventana.destroy()