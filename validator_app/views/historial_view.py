"""Vista: historial de consultas del usuario conectado."""

from tkinter import ttk

import customtkinter as ctk

from validator_app.controllers.historial_controller import HistorialController
from validator_app.views import theme


class HistorialView(ctk.CTkFrame):
    def __init__(self, master, controller: HistorialController):
        super().__init__(master, fg_color="transparent")
        self.controller = controller

        ctk.CTkLabel(self, text="Historial de consultas", font=theme.FUENTE_TITULO).grid(
            row=0, column=0, sticky="w", pady=(0, 16)
        )

        estilo = theme.estilo_tabla(self)
        columnas = ("fecha", "dni", "cobertura", "score", "riesgo")
        self.tabla = ttk.Treeview(self, columns=columnas, show="headings", style=estilo, height=18)
        for col, texto, ancho in (
            ("fecha", "Fecha", 160), ("dni", "DNI", 100), ("cobertura", "Cobertura", 90),
            ("score", "Score", 80), ("riesgo", "Riesgo", 160),
        ):
            self.tabla.heading(col, text=texto)
            self.tabla.column(col, width=ancho, anchor="w")
        self.tabla.grid(row=1, column=0, sticky="nsew")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.recargar()

    def recargar(self):
        self.tabla.delete(*self.tabla.get_children())
        for fila in self.controller.listar():
            riesgo = f"{fila['riesgo']} · {fila['calificacion']}" if fila["riesgo"] else "—"
            score = fila["score"] if fila["score"] is not None else "—"
            self.tabla.insert(
                "", "end",
                values=(fila["fecha"], fila["dni"], fila["cobertura"], score, riesgo),
            )
