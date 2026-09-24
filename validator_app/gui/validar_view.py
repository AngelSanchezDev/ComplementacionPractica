"""Vista: validar cobertura + score, con tarjeta de resultado."""

import customtkinter as ctk

from validator_app.core import db
from validator_app.gui import fields, theme


class ValidarView(ctk.CTkFrame):
    def __init__(self, master, conn, usuario, on_registrar_cliente):
        super().__init__(master, fg_color="transparent")
        self.conn = conn
        self.usuario = usuario
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
        validador = self.register(fields.permitir_digitos(8))
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

        ctk.CTkButton(formulario, text="VALIDAR", height=38, command=self._validar).grid(
            row=5, column=0, sticky="we", padx=20, pady=(12, 20)
        )

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

        self.btn_registrar = ctk.CTkButton(
            self.tarjeta, text="Registrar cliente", command=self._registrar_no_encontrado
        )
        self._dni_actual = ""

    def _validar(self):
        self.lbl_error.configure(text="")
        try:
            lat, lon = fields.parse_coordenadas(self.txt_coordenadas.get())
        except ValueError as exc:
            self.lbl_error.configure(text=str(exc))
            return
        try:
            dni = fields.validar_dni(self.txt_dni.get())
        except ValueError as exc:
            self.lbl_error.configure(text=str(exc))
            return
        self._dni_actual = dni
        usuario_id = self.usuario["id"] if self.usuario else None
        resultado = db.validar(self.conn, lat, lon, dni, usuario_id=usuario_id)
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
            self.btn_registrar.grid(row=6, column=0, sticky="w", padx=20, pady=(0, 20))

    def _registrar_no_encontrado(self):
        self.on_registrar_cliente(self._dni_actual)
