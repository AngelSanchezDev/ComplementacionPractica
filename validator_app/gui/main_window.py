"""Ventana principal de la aplicacion (CustomTkinter)."""

import customtkinter as ctk

from validator_app.core import db
from validator_app.gui import theme
from validator_app.gui.clientes_view import ClientesView
from validator_app.gui.historial_view import HistorialView
from validator_app.gui.login import LoginFrame
from validator_app.gui.validar_view import ValidarView


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        theme.configurar_tema()
        self.title("JSConnect Win Coverage")
        self.geometry("920x600")
        self.minsize(760, 520)
        self.conn = db.conectar()
        self.usuario = None
        self.vista_actual = None
        self._mostrar_login()

    # ---------- Login ----------
    def _mostrar_login(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.usuario = None
        login = LoginFrame(self, self.conn, on_login=self._al_iniciar_sesion)
        login.pack(fill="both", expand=True)

    def _al_iniciar_sesion(self, usuario):
        self.usuario = usuario
        self._construir_app()

    def _cerrar_sesion(self):
        self._mostrar_login()

    # ---------- App principal ----------
    def _construir_app(self):
        for widget in self.winfo_children():
            widget.destroy()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._construir_barra_lateral()

        self.contenedor = ctk.CTkFrame(self, fg_color="transparent")
        self.contenedor.grid(row=0, column=1, sticky="nsew", padx=24, pady=24)
        self.contenedor.grid_columnconfigure(0, weight=1)
        self.contenedor.grid_rowconfigure(0, weight=1)

        self._mostrar_vista_validar()

    def _construir_barra_lateral(self):
        barra = ctk.CTkFrame(self, width=200, corner_radius=0)
        barra.grid(row=0, column=0, sticky="nsw")
        barra.grid_propagate(False)

        ctk.CTkLabel(barra, text="JSConnect", font=theme.FUENTE_TITULO).pack(
            padx=20, pady=(28, 0), anchor="w"
        )
        ctk.CTkLabel(
            barra, text="Win Coverage", font=theme.FUENTE_SUBTITULO, text_color="gray60"
        ).pack(padx=20, pady=(0, 24), anchor="w")

        ctk.CTkButton(barra, text="Validar", anchor="w", command=self._mostrar_vista_validar).pack(
            fill="x", padx=16, pady=4
        )
        ctk.CTkButton(
            barra, text="Clientes", anchor="w", command=self._mostrar_vista_clientes
        ).pack(fill="x", padx=16, pady=4)
        ctk.CTkButton(
            barra, text="Historial", anchor="w", command=self._mostrar_vista_historial
        ).pack(fill="x", padx=16, pady=4)

        pie = ctk.CTkFrame(barra, fg_color="transparent")
        pie.pack(side="bottom", fill="x", padx=16, pady=16)
        ctk.CTkLabel(
            pie, text=f"Sesion: {self.usuario['usuario']}", font=theme.FUENTE_SUBTITULO
        ).pack(anchor="w")
        self.modo_oscuro_var = ctk.BooleanVar(value=ctk.get_appearance_mode() == "Dark")
        ctk.CTkSwitch(
            pie, text="Modo oscuro", variable=self.modo_oscuro_var,
            command=self._alternar_modo, width=0,
        ).pack(anchor="w", pady=(8, 8))
        ctk.CTkButton(
            pie, text="Cerrar sesion", fg_color="transparent", border_width=1,
            command=self._cerrar_sesion,
        ).pack(fill="x")

    def _alternar_modo(self):
        ctk.set_appearance_mode("dark" if self.modo_oscuro_var.get() else "light")
        vista = self.vista_actual
        if isinstance(vista, (ClientesView, HistorialView)):
            theme.estilo_tabla(self)

    def _limpiar_contenedor(self):
        for widget in self.contenedor.winfo_children():
            widget.destroy()

    def _mostrar_vista_validar(self):
        self._limpiar_contenedor()
        vista = ValidarView(self.contenedor, self.conn, self.usuario, self._ir_a_registrar_cliente)
        vista.grid(row=0, column=0, sticky="nsew")
        self.vista_actual = vista

    def _mostrar_vista_clientes(self):
        self._limpiar_contenedor()
        vista = ClientesView(self.contenedor, self.conn)
        vista.grid(row=0, column=0, sticky="nsew")
        self.vista_actual = vista

    def _mostrar_vista_historial(self):
        self._limpiar_contenedor()
        vista = HistorialView(self.contenedor, self.conn, self.usuario)
        vista.grid(row=0, column=0, sticky="nsew")
        self.vista_actual = vista

    def _ir_a_registrar_cliente(self, dni: str):
        self._mostrar_vista_clientes()
        self.vista_actual.abrir_nuevo_con_dni(dni)


def main():
    app = App()
    app.mainloop()
    return 0
