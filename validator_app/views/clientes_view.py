"""Vista: explorador de clientes con busqueda, paginacion y CRUD."""

import tkinter as tk
from tkinter import messagebox, ttk

import customtkinter as ctk

from validator_app.controllers.clientes_controller import ClientesController
from validator_app.views import theme
from validator_app.views.cliente_form import ClienteForm

LIMITE_PAGINA = 50
OPCIONES_RIESGO = ("Todos", "Muy Alto", "Alto", "Medio", "Bajo", "Muy Bajo")


class ClientesView(ctk.CTkFrame):
    def __init__(self, master, controller: ClientesController, riesgo_inicial: str | None = None):
        super().__init__(master, fg_color="transparent")
        self.controller = controller
        self.pagina = 0
        self._id_busqueda_pendiente = None
        self._id_copiado_pendiente = None

        ctk.CTkLabel(self, text="Clientes", font=theme.FUENTE_TITULO).grid(
            row=0, column=0, columnspan=5, sticky="w", pady=(0, 16)
        )

        self.txt_buscar = ctk.CTkEntry(
            self, placeholder_text="Buscar por DNI o nombre...", width=240
        )
        self.txt_buscar.grid(row=1, column=0, sticky="w")
        self.txt_buscar.bind("<KeyRelease>", self._buscar_con_espera)

        self.riesgo_var = ctk.StringVar(
            value=riesgo_inicial if riesgo_inicial in OPCIONES_RIESGO else "Todos"
        )
        ctk.CTkOptionMenu(
            self, values=list(OPCIONES_RIESGO), variable=self.riesgo_var,
            command=self._cambiar_riesgo, width=140,
        ).grid(row=1, column=1, padx=(8, 0))

        ctk.CTkButton(
            self, text="Nuevo", width=100, height=theme.ALTO_BOTON, font=theme.FUENTE_BOTON,
            command=self._nuevo,
        ).grid(row=1, column=2, padx=(8, 0))
        self.btn_editar = ctk.CTkButton(
            self, text="Editar", width=100, height=theme.ALTO_BOTON, font=theme.FUENTE_BOTON,
            command=self._editar, state="disabled",
        )
        self.btn_editar.grid(row=1, column=3, padx=(8, 0))
        self.btn_copiar = ctk.CTkButton(
            self, text="Copiar DNI", width=110, height=theme.ALTO_BOTON, font=theme.FUENTE_BOTON,
            command=self._copiar_dni_seleccionado, state="disabled",
        )
        self.btn_copiar.grid(row=1, column=4, padx=(8, 0))
        self.btn_eliminar = ctk.CTkButton(
            self, text="Eliminar", width=100, height=theme.ALTO_BOTON, font=theme.FUENTE_BOTON,
            fg_color="#c53030", hover_color="#9b2c2c",
            command=self._eliminar, state="disabled",
        )
        self.btn_eliminar.grid(row=1, column=5, padx=(8, 0))

        estilo = theme.estilo_tabla(self)
        columnas = ("dni", "nombre", "score", "riesgo")
        self.tabla = ttk.Treeview(
            self, columns=columnas, show="headings", style=estilo, height=16
        )
        for col, texto, ancho in (
            ("dni", "DNI", 100),
            ("nombre", "Nombre", 260),
            ("score", "Score", 80),
            ("riesgo", "Riesgo", 140),
        ):
            self.tabla.heading(col, text=texto)
            self.tabla.column(col, width=ancho, anchor="w")
        self.tabla.grid(row=2, column=0, columnspan=5, sticky="nsew", pady=(12, 8))
        self.tabla.bind("<<TreeviewSelect>>", self._seleccion_cambio)
        self.tabla.bind("<Double-1>", lambda _e: self._editar())
        self.tabla.bind("<Button-3>", self._abrir_menu_contextual)

        scrollbar_v = ttk.Scrollbar(self, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scrollbar_v.set)
        scrollbar_v.grid(row=2, column=5, sticky="ns", pady=(12, 8))

        self.menu_contextual = tk.Menu(self, tearoff=0)
        self.menu_contextual.add_command(label="Copiar DNI", command=self._copiar_dni_seleccionado)

        barra_paginas = ctk.CTkFrame(self, fg_color="transparent")
        barra_paginas.grid(row=3, column=0, columnspan=5, sticky="we")
        ctk.CTkButton(
            barra_paginas, text="< Anterior", width=100, height=theme.ALTO_BOTON,
            font=theme.FUENTE_BOTON, command=self._pagina_anterior,
        ).pack(side="left")
        self.lbl_contador = ctk.CTkLabel(barra_paginas, text="", font=theme.FUENTE_SUBTITULO)
        self.lbl_contador.pack(side="left", padx=12)
        ctk.CTkButton(
            barra_paginas, text="Siguiente >", width=100, height=theme.ALTO_BOTON,
            font=theme.FUENTE_BOTON, command=self._pagina_siguiente,
        ).pack(side="left")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        self.recargar()

    def _buscar_con_espera(self, _event=None):
        if self._id_busqueda_pendiente:
            self.after_cancel(self._id_busqueda_pendiente)
        self._id_busqueda_pendiente = self.after(300, self._buscar)

    def _buscar(self):
        self.pagina = 0
        self.recargar()

    def _cambiar_riesgo(self, _valor=None):
        self.pagina = 0
        self.recargar()

    def recargar(self):
        texto = self.txt_buscar.get()
        riesgo = self.riesgo_var.get()
        riesgo = None if riesgo == "Todos" else riesgo
        filas, total = self.controller.buscar(
            texto, riesgo_filtro=riesgo,
            limite=LIMITE_PAGINA, offset=self.pagina * LIMITE_PAGINA,
        )
        self.tabla.delete(*self.tabla.get_children())
        for fila in filas:
            self.tabla.insert(
                "", "end", iid=fila["dni"],
                values=(fila["dni"], fila["nombre"], fila["score"], fila["riesgo"] or "—"),
            )
        inicio = self.pagina * LIMITE_PAGINA + (1 if total else 0)
        fin = min(inicio + len(filas) - 1, total) if filas else inicio - 1
        self.lbl_contador.configure(text=f"{inicio}\u2013{fin} de {total}")
        self._total_actual = total
        self._seleccion_cambio()

    def _seleccion_cambio(self, _event=None):
        hay_seleccion = bool(self.tabla.selection())
        estado = "normal" if hay_seleccion else "disabled"
        self.btn_editar.configure(state=estado)
        self.btn_eliminar.configure(state=estado)
        self.btn_copiar.configure(state=estado)

    def _dni_seleccionado(self) -> str | None:
        seleccion = self.tabla.selection()
        return seleccion[0] if seleccion else None

    def _abrir_menu_contextual(self, event):
        fila = self.tabla.identify_row(event.y)
        if not fila:
            return
        self.tabla.selection_set(fila)
        self.menu_contextual.tk_popup(event.x_root, event.y_root)

    def _copiar_dni_seleccionado(self):
        dni = self._dni_seleccionado()
        if not dni:
            return
        theme.copiar_al_portapapeles(self, dni)
        texto_original = self.btn_copiar.cget("text")
        self.btn_copiar.configure(text="¡Copiado!")
        if self._id_copiado_pendiente:
            self.after_cancel(self._id_copiado_pendiente)
        self._id_copiado_pendiente = self.after(
            1000, lambda: self.btn_copiar.configure(text=texto_original)
        )

    def _nuevo(self):
        ClienteForm(self, self.controller, on_guardado=self.recargar)

    def _editar(self):
        dni = self._dni_seleccionado()
        if dni:
            ClienteForm(
                self, self.controller, on_guardado=self.recargar, dni_inicial=dni, editar=True
            )

    def _eliminar(self):
        dni = self._dni_seleccionado()
        if not dni:
            return
        if messagebox.askyesno("Eliminar cliente", f"¿Eliminar el cliente con DNI {dni}?"):
            self.controller.eliminar(dni)
            self.recargar()

    def _pagina_anterior(self):
        if self.pagina > 0:
            self.pagina -= 1
            self.recargar()

    def _pagina_siguiente(self):
        if (self.pagina + 1) * LIMITE_PAGINA < getattr(self, "_total_actual", 0):
            self.pagina += 1
            self.recargar()

    def abrir_nuevo_con_dni(self, dni: str):
        ClienteForm(
            self, self.controller, on_guardado=self.recargar, dni_inicial=dni, editar=False
        )
