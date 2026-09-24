"""Vista: catalogo de consultas predefinidas con distintos tipos de JOIN."""

from tkinter import ttk

import customtkinter as ctk

from validator_app.controllers.consultas_controller import ConsultasController
from validator_app.views import theme


class ConsultasView(ctk.CTkFrame):
    def __init__(self, master, controller: ConsultasController):
        super().__init__(master, fg_color="transparent")
        self.controller = controller
        self.catalogo = controller.catalogo()

        ctk.CTkLabel(self, text="Consultas SQL", font=theme.FUENTE_TITULO).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 16)
        )

        self.claves = list(self.catalogo)
        titulos = [self.catalogo[clave]["titulo"] for clave in self.claves]

        self.consulta_var = ctk.StringVar(value=titulos[0])
        ctk.CTkOptionMenu(
            self, values=titulos, variable=self.consulta_var,
            command=self._cambiar_consulta, width=340,
        ).grid(row=1, column=0, sticky="w")

        ctk.CTkButton(
            self, text="Ejecutar", width=120, height=theme.ALTO_BOTON, font=theme.FUENTE_BOTON,
            command=self._ejecutar,
        ).grid(row=1, column=1, sticky="w", padx=(8, 0))

        self.lbl_tipo_join = ctk.CTkLabel(self, text="", font=theme.FUENTE_ETIQUETA)
        self.lbl_tipo_join.grid(row=2, column=0, columnspan=2, sticky="w", pady=(12, 2))

        self.lbl_descripcion = ctk.CTkLabel(
            self, text="", font=theme.FUENTE_SUBTITULO, text_color="gray60",
            wraplength=560, justify="left",
        )
        self.lbl_descripcion.grid(row=3, column=0, columnspan=2, sticky="w", pady=(0, 8))

        self.txt_sql = ctk.CTkTextbox(self, height=110, font=("Consolas", 12))
        self.txt_sql.grid(row=4, column=0, columnspan=2, sticky="we", pady=(0, 12))
        self.txt_sql.configure(state="disabled")

        frame_tabla = ctk.CTkFrame(self, corner_radius=12)
        frame_tabla.grid(row=5, column=0, columnspan=2, sticky="nsew")
        frame_tabla.columnconfigure(0, weight=1)
        frame_tabla.rowconfigure(0, weight=1)

        estilo = theme.estilo_tabla(self)
        self.tabla = ttk.Treeview(frame_tabla, show="headings", style=estilo, height=14)
        self.tabla.grid(row=0, column=0, sticky="nsew", padx=(12, 0), pady=12)
        scrollbar_v = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scrollbar_v.set)
        scrollbar_v.grid(row=0, column=1, sticky="ns", pady=12, padx=(0, 12))

        self.lbl_total = ctk.CTkLabel(self, text="", font=theme.FUENTE_SUBTITULO)
        self.lbl_total.grid(row=6, column=0, columnspan=2, sticky="w", pady=(8, 0))

        self.columnconfigure(0, weight=1)
        self.rowconfigure(5, weight=1)

        self._cambiar_consulta(titulos[0])
        self._ejecutar()

    def _clave_actual(self) -> str:
        titulo = self.consulta_var.get()
        for clave in self.claves:
            if self.catalogo[clave]["titulo"] == titulo:
                return clave
        return self.claves[0]

    def _cambiar_consulta(self, _titulo):
        entrada = self.catalogo[self._clave_actual()]
        self.lbl_tipo_join.configure(text=entrada["tipo_join"])
        self.lbl_descripcion.configure(text=entrada["descripcion"])
        self.txt_sql.configure(state="normal")
        self.txt_sql.delete("1.0", "end")
        self.txt_sql.insert("1.0", entrada["sql"])
        self.txt_sql.configure(state="disabled")

    def _ejecutar(self):
        columnas, filas = self.controller.ejecutar(self._clave_actual())
        self.tabla.delete(*self.tabla.get_children())
        self.tabla["columns"] = columnas
        for col in columnas:
            self.tabla.heading(col, text=col)
            self.tabla.column(col, width=140, anchor="w")
        for fila in filas:
            self.tabla.insert("", "end", values=fila)
        self.lbl_total.configure(text=f"{len(filas)} fila(s)")
