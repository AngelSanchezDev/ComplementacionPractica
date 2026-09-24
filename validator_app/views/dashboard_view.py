"""Vista: dashboard con el porcentaje de clientes por nivel de riesgo."""

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from validator_app.controllers.dashboard_controller import DashboardController
from validator_app.views import theme


class DashboardView(ctk.CTkFrame):
    def __init__(self, master, controller: DashboardController, on_ver_riesgo):
        super().__init__(master, fg_color="transparent")
        self.controller = controller
        self.on_ver_riesgo = on_ver_riesgo

        ctk.CTkLabel(self, text="Dashboard", font=theme.FUENTE_TITULO).grid(
            row=0, column=0, sticky="w", pady=(0, 16)
        )

        self.frame_tarjetas = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_tarjetas.grid(row=1, column=0, sticky="we", pady=(0, 16))

        self.frame_grafico = ctk.CTkFrame(self, corner_radius=12)
        self.frame_grafico.grid(row=2, column=0, sticky="nsew")
        self.frame_grafico.columnconfigure(0, weight=1)
        self.frame_grafico.rowconfigure(0, weight=1)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self._canvas_grafico = None
        self.recargar()

    def recargar(self):
        resumen = self.controller.resumen()
        total = sum(fila["total"] for fila in resumen) or 1

        for widget in self.frame_tarjetas.winfo_children():
            widget.destroy()
        for i, fila in enumerate(resumen):
            porcentaje = fila["total"] / total * 100
            tarjeta = ctk.CTkFrame(self.frame_tarjetas, corner_radius=10)
            tarjeta.grid(row=0, column=i, padx=(0, 10) if i < len(resumen) - 1 else 0, sticky="we")
            self.frame_tarjetas.columnconfigure(i, weight=1)
            barra_color = ctk.CTkFrame(
                tarjeta, fg_color=theme.color_riesgo(fila["riesgo"]), height=6, corner_radius=3
            )
            barra_color.pack(fill="x", padx=10, pady=(10, 6))
            ctk.CTkLabel(tarjeta, text=fila["riesgo"], font=theme.FUENTE_ETIQUETA).pack(
                anchor="w", padx=10
            )
            ctk.CTkLabel(
                tarjeta, text=f"{porcentaje:.1f}%  ({fila['total']})", font=theme.FUENTE_NORMAL
            ).pack(anchor="w", padx=10, pady=(0, 10))
            tarjeta.bind("<Button-1>", lambda _e, r=fila["riesgo"]: self.on_ver_riesgo(r))
            for hijo in tarjeta.winfo_children():
                hijo.bind("<Button-1>", lambda _e, r=fila["riesgo"]: self.on_ver_riesgo(r))
            tarjeta.configure(cursor="hand2")

        self._dibujar_grafico(resumen, total)

    def _dibujar_grafico(self, resumen, total):
        if self._canvas_grafico is not None:
            self._canvas_grafico.get_tk_widget().destroy()

        colores_modo = theme.colores_modo()
        riesgos = [f["riesgo"] for f in resumen]
        porcentajes = [f["total"] / total * 100 for f in resumen]
        colores = [theme.color_riesgo(r) for r in riesgos]

        figura = Figure(figsize=(7, 3.6), dpi=100)
        figura.patch.set_facecolor(colores_modo["fondo"])
        ejes = figura.add_subplot(111)
        ejes.set_facecolor(colores_modo["fondo"])

        barras = ejes.barh(riesgos, porcentajes, color=colores)
        for barra, porcentaje in zip(barras, porcentajes, strict=True):
            ejes.text(
                barra.get_width() + 1, barra.get_y() + barra.get_height() / 2,
                f"{porcentaje:.1f}%", va="center", color=colores_modo["texto"], fontsize=10,
            )
        ejes.set_xlim(0, max(porcentajes, default=0) + 12)
        ejes.set_xlabel("Porcentaje de clientes", color=colores_modo["texto"])
        ejes.tick_params(colors=colores_modo["texto"])
        for spine in ejes.spines.values():
            spine.set_color(colores_modo["texto"])
        figura.tight_layout()

        self._canvas_grafico = FigureCanvasTkAgg(figura, master=self.frame_grafico)
        self._canvas_grafico.draw()
        widget = self._canvas_grafico.get_tk_widget()
        widget.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        def al_hacer_clic(evento):
            if evento.inaxes != ejes:
                return
            indice = round(evento.ydata)
            if 0 <= indice < len(riesgos):
                self.on_ver_riesgo(riesgos[indice])

        self._canvas_grafico.mpl_connect("button_press_event", al_hacer_clic)
