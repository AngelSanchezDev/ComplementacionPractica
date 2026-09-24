"""Formulario modal para crear/editar un cliente (CRUD)."""

import customtkinter as ctk

from validator_app.controllers.clientes_controller import ClientesController
from validator_app.models.errors import APIError
from validator_app.views import entrada, theme


class ClienteForm(ctk.CTkToplevel):
    def __init__(
        self,
        master,
        controller: ClientesController,
        on_guardado,
        dni_inicial: str | None = None,
        editar=False,
    ):
        super().__init__(master)
        self.controller = controller
        self.on_guardado = on_guardado
        self.editar = editar
        self.dni_original = dni_inicial if editar else None

        self.title("Editar cliente" if editar else "Nuevo cliente")
        self.geometry("360x360")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=24, pady=24)

        ctk.CTkLabel(frame, text="DNI:", font=theme.FUENTE_ETIQUETA).pack(anchor="w")
        validador = self.register(entrada.permitir_digitos(8))
        self.txt_dni = ctk.CTkEntry(
            frame, validate="key", validatecommand=(validador, "%P")
        )
        self.txt_dni.pack(fill="x", pady=(2, 4))
        if dni_inicial:
            self.txt_dni.insert(0, dni_inicial)
        if editar:
            self.txt_dni.configure(state="disabled")
        else:
            self.txt_dni.bind("<KeyRelease>", self._revisar_dni_duplicado)

        self.lbl_dni_estado = ctk.CTkLabel(frame, text="", font=theme.FUENTE_SUBTITULO)
        self.lbl_dni_estado.pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(frame, text="Nombre completo:", font=theme.FUENTE_ETIQUETA).pack(anchor="w")
        self.txt_nombre = ctk.CTkEntry(frame)
        self.txt_nombre.pack(fill="x", pady=(2, 8))

        ctk.CTkLabel(frame, text="Score (0 a 1000):", font=theme.FUENTE_ETIQUETA).pack(anchor="w")
        validador_score = self.register(entrada.permitir_digitos(4))
        self.txt_score = ctk.CTkEntry(
            frame, validate="key", validatecommand=(validador_score, "%P")
        )
        self.txt_score.pack(fill="x", pady=(2, 4))
        self.txt_score.bind("<KeyRelease>", self._previsualizar_riesgo)

        self.lbl_riesgo_preview = ctk.CTkLabel(frame, text="", font=theme.FUENTE_SUBTITULO)
        self.lbl_riesgo_preview.pack(anchor="w", pady=(0, 8))

        self.lbl_error = ctk.CTkLabel(frame, text="", text_color="#e5484d")
        self.lbl_error.pack(anchor="w", pady=(4, 4))

        self.btn_guardar = ctk.CTkButton(
            frame, text="Guardar", height=theme.ALTO_BOTON, font=theme.FUENTE_BOTON,
            command=self._guardar,
        )
        self.btn_guardar.pack(fill="x", pady=(8, 0))

        if editar:
            cliente = self.controller.obtener(dni_inicial)
            if cliente:
                self.txt_nombre.insert(0, cliente["nombre"])
                self.txt_score.insert(0, str(cliente["score"]))
                self._previsualizar_riesgo()

    def _revisar_dni_duplicado(self, _event=None):
        dni = self.txt_dni.get().strip()
        if self.controller.existe(dni):
            self.lbl_dni_estado.configure(text="El DNI ya esta registrado.", text_color="#e5484d")
        else:
            self.lbl_dni_estado.configure(text="")

    def _previsualizar_riesgo(self, _event=None):
        info = self.controller.clasificar_preview(self.txt_score.get().strip())
        if info is None:
            self.lbl_riesgo_preview.configure(text="")
            return
        self.lbl_riesgo_preview.configure(
            text=f"Riesgo {info['riesgo']} · {info['calificacion']}",
            text_color=theme.color_riesgo(info["riesgo"]),
        )

    def _guardar(self):
        self.lbl_error.configure(text="")
        try:
            if self.editar:
                self.controller.actualizar(
                    self.txt_dni.get(), self.txt_nombre.get(), self.txt_score.get()
                )
            else:
                self.controller.crear(
                    self.txt_dni.get(), self.txt_nombre.get(), self.txt_score.get()
                )
        except APIError as exc:
            self.lbl_error.configure(text=str(exc))
            return
        self.on_guardado()
        self.destroy()
