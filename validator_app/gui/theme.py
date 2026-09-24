"""Colores y fuentes compartidos por la interfaz CustomTkinter."""

from tkinter import ttk

import customtkinter as ctk

COLOR_RIESGO = {
    "Muy Alto": "#e5484d",
    "Alto": "#f76b15",
    "Medio": "#e2a336",
    "Bajo": "#30a46c",
    "Muy Bajo": "#18794e",
}

COLOR_TEXTO_CLARO = "#ffffff"

FUENTE_TITULO = ("Segoe UI", 22, "bold")
FUENTE_SUBTITULO = ("Segoe UI", 13)
FUENTE_SCORE = ("Segoe UI", 40, "bold")
FUENTE_NORMAL = ("Segoe UI", 13)
FUENTE_ETIQUETA = ("Segoe UI", 12, "bold")


def color_riesgo(riesgo: str | None) -> str:
    return COLOR_RIESGO.get(riesgo or "", "#888888")


def configurar_tema() -> None:
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")


def estilo_tabla(root) -> str:
    """Configura ttk.Treeview para que combine con el modo claro/oscuro.

    Devuelve el nombre de estilo.
    """
    oscuro = ctk.get_appearance_mode() == "Dark"
    fondo = "#1a1a1a" if oscuro else "#ffffff"
    texto = "#dcdcdc" if oscuro else "#1a1a1a"
    fondo_cabecera = "#2b2b2b" if oscuro else "#e5e5e5"
    seleccion = "#144870" if oscuro else "#b7d9f7"

    estilo = ttk.Style(root)
    estilo.theme_use("default")
    estilo.configure(
        "JSC.Treeview",
        background=fondo,
        fieldbackground=fondo,
        foreground=texto,
        rowheight=28,
        borderwidth=0,
        font=FUENTE_NORMAL,
    )
    estilo.configure(
        "JSC.Treeview.Heading",
        background=fondo_cabecera,
        foreground=texto,
        font=FUENTE_ETIQUETA,
        borderwidth=0,
    )
    estilo.map("JSC.Treeview", background=[("selected", seleccion)])
    return "JSC.Treeview"
