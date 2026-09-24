"""Vista: explorador de clientes con busqueda, paginacion y CRUD."""

from tkinter import messagebox, ttk

import customtkinter as ctk

from validator_app.core import db
from validator_app.gui import theme
from validator_app.gui.cliente_form import ClienteForm

LIMITE_PAGINA = 50


class ClientesView(ctk.CTkFrame):
    def __init__(self, master, conn):
        super().__init__(master, fg_color="transparent")
        self.conn = conn
        self.pagina = 0
        self._id_busqueda_pendiente = None

        ctk.CTkLabel(self, text="Clientes", font=theme.FUENTE_TITULO).grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 16)
        )

        self.txt_buscar = ctk.CTkEntry(
            self, placeholder_text="Buscar por DNI o nombre...", width=280
        )
        self.txt_buscar.grid(row=1, column=0, sticky="w")
        self.txt_buscar.bind("<KeyRelease>", self._buscar_con_espera)

        ctk.CTkButton(self, text="Nuevo", width=90, command=self._nuevo).grid(
            row=1, column=1, padx=(8, 0)
        )
        self.btn_editar = ctk.CTkButton(
            self, text="Editar", width=90, command=self._editar, state="disabled"
        )
        self.btn_editar.grid(row=1, column=2, padx=(8, 0))
        self.btn_eliminar = ctk.CTkButton(
            self, text="Eliminar", width=90, fg_color="#c53030", hover_color="#9b2c2c",
            command=self._eliminar, state="disabled",
        )
        self.btn_eliminar.grid(row=1, column=3, padx=(8, 0))

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
        self.tabla.grid(row=2, column=0, columnspan=4, sticky="nsew", pady=(12, 8))
        self.tabla.bind("<<TreeviewSelect>>", self._seleccion_cambio)
        self.tabla.bind("<Double-1>", lambda _e: self._editar())

        barra_paginas = ctk.CTkFrame(self, fg_color="transparent")
        barra_paginas.grid(row=3, column=0, columnspan=4, sticky="we")
        ctk.CTkButton(
            barra_paginas, text="< Anterior", width=100, command=self._pagina_anterior
        ).pack(side="left")
        self.lbl_contador = ctk.CTkLabel(barra_paginas, text="", font=theme.FUENTE_SUBTITULO)
        self.lbl_contador.pack(side="left", padx=12)
        ctk.CTkButton(
            barra_paginas, text="Siguiente >", width=100, command=self._pagina_siguiente
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

    def recargar(self):
        texto = self.txt_buscar.get()
        filas, total = db.buscar_clientes(
            self.conn, texto, limite=LIMITE_PAGINA, offset=self.pagina * LIMITE_PAGINA
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

    def _dni_seleccionado(self) -> str | None:
        seleccion = self.tabla.selection()
        return seleccion[0] if seleccion else None

    def _nuevo(self):
        ClienteForm(self, self.conn, on_guardado=self.recargar)

    def _editar(self):
        dni = self._dni_seleccionado()
        if dni:
            ClienteForm(self, self.conn, on_guardado=self.recargar, dni_inicial=dni, editar=True)

    def _eliminar(self):
        dni = self._dni_seleccionado()
        if not dni:
            return
        if messagebox.askyesno("Eliminar cliente", f"¿Eliminar el cliente con DNI {dni}?"):
            db.eliminar_cliente(self.conn, dni)
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
        ClienteForm(self, self.conn, on_guardado=self.recargar, dni_inicial=dni, editar=False)
