"""Ventana principal de la aplicacion (CustomTkinter). Vista raiz: abre la
conexion, guarda la sesion y arma el Controlador de cada pantalla antes de
mostrarla."""

import customtkinter as ctk

from validator_app.controllers.clientes_controller import ClientesController
from validator_app.controllers.consultas_controller import ConsultasController
from validator_app.controllers.dashboard_controller import DashboardController
from validator_app.controllers.historial_controller import HistorialController
from validator_app.controllers.login_controller import LoginController
from validator_app.controllers.validar_controller import ValidarController
from validator_app.models import database
from validator_app.views import theme
from validator_app.views.clientes_view import ClientesView
from validator_app.views.consultas_view import ConsultasView
from validator_app.views.dashboard_view import DashboardView
from validator_app.views.historial_view import HistorialView
from validator_app.views.login_view import LoginFrame
from validator_app.views.validar_view import ValidarView


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        theme.configurar_tema()
        self.title("JSConnect Win Coverage")
        self.geometry("920x600")
        self.minsize(760, 520)
        self.conn = database.conectar()
        self.usuario = None
        self.vista_actual = None
        self._mostrar_login()

    # ---------- Login ----------
    def _mostrar_login(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.usuario = None
        controller = LoginController(self.conn)
        login = LoginFrame(self, controller, on_login=self._al_iniciar_sesion)
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

        botones_nav = (
            ("Validar", self._mostrar_vista_validar),
            ("Dashboard", self._mostrar_vista_dashboard),
            ("Clientes", self._mostrar_vista_clientes),
            ("Historial", self._mostrar_vista_historial),
            ("Consultas SQL", self._mostrar_vista_consultas),
        )
        for texto, comando in botones_nav:
            ctk.CTkButton(
                barra, text=texto, anchor="w", height=theme.ALTO_BOTON, font=theme.FUENTE_BOTON,
                command=comando,
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
            height=theme.ALTO_BOTON, font=theme.FUENTE_BOTON,
            command=self._cerrar_sesion,
        ).pack(fill="x")

    def _alternar_modo(self):
        ctk.set_appearance_mode("dark" if self.modo_oscuro_var.get() else "light")
        vista = self.vista_actual
        if isinstance(vista, (ClientesView, HistorialView, ConsultasView)):
            theme.estilo_tabla(self)
        elif isinstance(vista, DashboardView):
            vista.recargar()

    def _limpiar_contenedor(self):
        for widget in self.contenedor.winfo_children():
            widget.destroy()

    def _mostrar_vista_validar(self):
        self._limpiar_contenedor()
        controller = ValidarController(self.conn, self.usuario)
        vista = ValidarView(self.contenedor, controller, self._ir_a_registrar_cliente)
        vista.grid(row=0, column=0, sticky="nsew")
        self.vista_actual = vista

    def _mostrar_vista_clientes(self, riesgo_inicial: str | None = None):
        self._limpiar_contenedor()
        controller = ClientesController(self.conn)
        vista = ClientesView(self.contenedor, controller, riesgo_inicial=riesgo_inicial)
        vista.grid(row=0, column=0, sticky="nsew")
        self.vista_actual = vista

    def _mostrar_vista_historial(self):
        self._limpiar_contenedor()
        controller = HistorialController(self.conn, self.usuario)
        vista = HistorialView(self.contenedor, controller)
        vista.grid(row=0, column=0, sticky="nsew")
        self.vista_actual = vista

    def _mostrar_vista_dashboard(self):
        self._limpiar_contenedor()
        controller = DashboardController(self.conn)
        vista = DashboardView(self.contenedor, controller, self._ir_a_clientes_por_riesgo)
        vista.grid(row=0, column=0, sticky="nsew")
        self.vista_actual = vista

    def _mostrar_vista_consultas(self):
        self._limpiar_contenedor()
        controller = ConsultasController(self.conn)
        vista = ConsultasView(self.contenedor, controller)
        vista.grid(row=0, column=0, sticky="nsew")
        self.vista_actual = vista

    def _ir_a_registrar_cliente(self, dni: str):
        self._mostrar_vista_clientes()
        self.vista_actual.abrir_nuevo_con_dni(dni)

    def _ir_a_clientes_por_riesgo(self, riesgo: str):
        self._mostrar_vista_clientes(riesgo_inicial=riesgo)


def main():
    app = App()
    app.mainloop()
    return 0
