"""Pantalla de inicio de sesion (tarjeta centrada, sin ventanas emergentes)."""

import customtkinter as ctk

from validator_app.core import db
from validator_app.gui import theme


class LoginFrame(ctk.CTkFrame):
    def __init__(self, master, conn, on_login):
        super().__init__(master, fg_color="transparent")
        self.conn = conn
        self.on_login = on_login

        tarjeta = ctk.CTkFrame(self, corner_radius=16, width=360)
        tarjeta.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(tarjeta, text="JSConnect Win Coverage", font=theme.FUENTE_TITULO).pack(
            padx=32, pady=(32, 4)
        )
        ctk.CTkLabel(
            tarjeta,
            text="Inicia sesion para validar cobertura y score",
            font=theme.FUENTE_SUBTITULO,
            text_color="gray60",
        ).pack(padx=32, pady=(0, 24))

        self.txt_usuario = ctk.CTkEntry(tarjeta, placeholder_text="Usuario", width=280)
        self.txt_usuario.pack(padx=32, pady=(0, 12))

        frame_password = ctk.CTkFrame(tarjeta, fg_color="transparent")
        frame_password.pack(padx=32, pady=(0, 4))
        self.txt_password = ctk.CTkEntry(
            frame_password, placeholder_text="Contraseña", show="•", width=280
        )
        self.txt_password.pack()

        self.mostrar_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            tarjeta,
            text="Mostrar contraseña",
            variable=self.mostrar_var,
            command=self._toggle_password,
            font=theme.FUENTE_SUBTITULO,
        ).pack(padx=32, pady=(4, 4), anchor="w")

        self.lbl_error = ctk.CTkLabel(
            tarjeta, text="", text_color="#e5484d", font=theme.FUENTE_SUBTITULO
        )
        self.lbl_error.pack(padx=32, pady=(4, 8))

        ctk.CTkButton(
            tarjeta, text="Ingresar", command=self._ingresar, width=280, height=38
        ).pack(padx=32, pady=(4, 32))

        self.txt_usuario.bind("<Return>", lambda _e: self._ingresar())
        self.txt_password.bind("<Return>", lambda _e: self._ingresar())
        self.txt_usuario.focus_set()

    def _toggle_password(self):
        self.txt_password.configure(show="" if self.mostrar_var.get() else "•")

    def _ingresar(self):
        usuario = db.autenticar(self.conn, self.txt_usuario.get(), self.txt_password.get())
        if usuario is None:
            self.lbl_error.configure(text="Usuario o contraseña incorrectos.")
            self.txt_password.delete(0, "end")
            return
        self.lbl_error.configure(text="")
        self.on_login(usuario)
