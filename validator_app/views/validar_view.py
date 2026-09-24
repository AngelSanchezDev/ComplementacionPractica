"""Vista: validar cobertura + score, con tarjeta de resultado."""

import customtkinter as ctk

from validator_app.controllers.validar_controller import ValidarController
from validator_app.models.errors import APIError
from validator_app.views import entrada, theme


class ValidarView(ctk.CTkFrame):
    def __init__(self, master, controller: ValidarController, on_registrar_cliente):
        super().__init__(master, fg_color="transparent")
        self.controller = controller
        self.on_registrar_cliente = on_registrar_cliente

        ctk.CTkLabel(self, text="Validar cliente", font=theme.FUENTE_TITULO).grid(
            row=0, column=0, sticky="w", pady=(0, 16)
        )

        formulario = ctk.CTkFrame(self, corner_radius=12)
        formulario.grid(row=1, column=0, sticky="new", pady=(0, 16))
        formulario.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            formulario, text="Coordenadas (latitud, longitud):", font=theme.FUENTE_ETIQUETA
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 4))
        self.txt_coordenadas = ctk.CTkEntry(
            formulario, placeholder_text="-11.956037, -77.040653"
        )
        self.txt_coordenadas.grid(row=1, column=0, sticky="we", padx=20)

        ctk.CTkLabel(formulario, text="DNI:", font=theme.FUENTE_ETIQUETA).grid(
            row=2, column=0, sticky="w", padx=20, pady=(16, 4)
        )
        validador = self.register(entrada.permitir_digitos(8))
        self.txt_dni = ctk.CTkEntry(
            formulario,
            placeholder_text="8 digitos",
            validate="key",
            validatecommand=(validador, "%P"),
        )
        self.txt_dni.grid(row=3, column=0, sticky="we", padx=20)
        self.txt_dni.bind("<Return>", lambda _e: self._validar())

        self.lbl_error = ctk.CTkLabel(formulario, text="", text_color="#e5484d")
        self.lbl_error.grid(row=4, column=0, sticky="w", padx=20, pady=(8, 0))

        ctk.CTkButton(
            formulario, text="VALIDAR", height=theme.ALTO_BOTON, font=theme.FUENTE_BOTON,
            command=self._validar,
        ).grid(row=5, column=0, sticky="we", padx=20, pady=(12, 20))

        self._construir_tarjeta_resultado()
        self.columnconfigure(0, weight=1)

    def _construir_tarjeta_resultado(self):
        self.tarjeta = ctk.CTkFrame(self, corner_radius=12)
        self.tarjeta.grid(row=2, column=0, sticky="new")
        self.tarjeta.columnconfigure(0, weight=1)

        ctk.CTkLabel(self.tarjeta, text="Resultado", font=theme.FUENTE_ETIQUETA).grid(
            row=0, column=0, sticky="w", padx=20, pady=(16, 8)
        )
        self.lbl_cobertura = ctk.CTkLabel(
            self.tarjeta, text="Cobertura: —", font=theme.FUENTE_NORMAL
        )
        self.lbl_cobertura.grid(row=1, column=0, sticky="w", padx=20)

        self.lbl_score = ctk.CTkLabel(self.tarjeta, text="—", font=theme.FUENTE_SCORE)
        self.lbl_score.grid(row=2, column=0, sticky="w", padx=20, pady=(12, 0))

        self.barra_score = ctk.CTkProgressBar(self.tarjeta, width=320)
        self.barra_score.set(0)
        self.barra_score.grid(row=3, column=0, sticky="we", padx=20, pady=(8, 4))

        self.lbl_riesgo = ctk.CTkLabel(self.tarjeta, text="", font=theme.FUENTE_NORMAL)
        self.lbl_riesgo.grid(row=4, column=0, sticky="w", padx=20)

        self.lbl_cliente = ctk.CTkLabel(
            self.tarjeta, text="", font=theme.FUENTE_NORMAL, text_color="gray60"
        )
        self.lbl_cliente.grid(row=5, column=0, sticky="w", padx=20, pady=(0, 8))

        self.btn_copiar_dni = ctk.CTkButton(
            self.tarjeta, text="Copiar DNI", width=130,
            height=theme.ALTO_BOTON, font=theme.FUENTE_BOTON,
            command=self._copiar_dni,
        )
        self.btn_registrar = ctk.CTkButton(
            self.tarjeta, text="Registrar cliente",
            height=theme.ALTO_BOTON, font=theme.FUENTE_BOTON,
            command=self._registrar_no_encontrado,
        )
        self._dni_actual = ""
        self._id_copiado_pendiente = None

    def _validar(self):
        self.lbl_error.configure(text="")
        try:
            resultado = self.controller.validar(self.txt_coordenadas.get(), self.txt_dni.get())
        except APIError as exc:
            self.lbl_error.configure(text=str(exc))
            return
        self._dni_actual = self.txt_dni.get().strip()
        self._mostrar_resultado(resultado)

    def _mostrar_resultado(self, resultado):
        cobertura = resultado["cobertura"]
        self.lbl_cobertura.configure(
            text=f"Cobertura: {'SI' if cobertura['hay_cobertura'] else 'NO'}"
        )
        score = resultado.get("score")
        self.btn_registrar.grid_forget()
        if score:
            color = theme.color_riesgo(score["riesgo"])
            self.lbl_score.configure(text=str(score["valor"]), text_color=color)
            self.barra_score.set(score["valor"] / 1000)
            self.barra_score.configure(progress_color=color)
            self.lbl_riesgo.configure(
                text=f"Riesgo {score['riesgo']} · {score['calificacion']}",
                text_color=theme.color_riesgo(score["riesgo"]),
            )
            self.lbl_cliente.configure(text=score["nombre"])
        else:
            self.lbl_score.configure(text="—", text_color=("black", "white"))
            self.barra_score.set(0)
            self.lbl_riesgo.configure(text="DNI no registrado", text_color="#e5484d")
            self.lbl_cliente.configure(text="")
        self.btn_copiar_dni.grid(row=6, column=0, sticky="w", padx=20, pady=(0, 8))
        if not score:
            self.btn_registrar.grid(row=7, column=0, sticky="w", padx=20, pady=(0, 20))

    def _copiar_dni(self):
        if not self._dni_actual:
            return
        theme.copiar_al_portapapeles(self, self._dni_actual)
        texto_original = self.btn_copiar_dni.cget("text")
        self.btn_copiar_dni.configure(text="¡Copiado!")
        if self._id_copiado_pendiente:
            self.after_cancel(self._id_copiado_pendiente)
        self._id_copiado_pendiente = self.after(
            1000, lambda: self.btn_copiar_dni.configure(text=texto_original)
        )

    def _registrar_no_encontrado(self):
        self.on_registrar_cliente(self._dni_actual)
