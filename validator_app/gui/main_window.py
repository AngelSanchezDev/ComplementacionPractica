"""Ventana principal de la aplicacion."""

import tkinter as tk
from tkinter import messagebox, ttk

from validator_app.core import db
from validator_app.gui import fields


class LoginDialog(tk.Toplevel):
    """Dialogo modal de inicio de sesion contra la BD local."""

    def __init__(self, parent: tk.Tk, conn):
        super().__init__(parent)
        self.conn = conn
        self.usuario = None
        self.title("Iniciar sesion")
        self.geometry("320x180")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        frame = ttk.Frame(self, padding=16)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Usuario:").grid(row=0, column=0, sticky="w", pady=4)
        self.txt_usuario = ttk.Entry(frame)
        self.txt_usuario.grid(row=0, column=1, sticky="we", pady=4)
        ttk.Label(frame, text="Contraseña:").grid(row=1, column=0, sticky="w", pady=4)
        self.txt_password = ttk.Entry(frame, show="•")
        self.txt_password.grid(row=1, column=1, sticky="we", pady=4)
        ttk.Button(frame, text="Ingresar", command=self._ingresar).grid(
            row=2, column=0, columnspan=2, sticky="we", pady=(12, 0)
        )

        self.bind("<Return>", lambda _e: self._ingresar())
        self.txt_usuario.focus_set()
        self.grab_set()

    def _ingresar(self):
        usuario = db.autenticar(self.conn, self.txt_usuario.get(), self.txt_password.get())
        if usuario is None:
            messagebox.showerror("Login", "Usuario o contraseña incorrectos.", parent=self)
            self.txt_password.delete(0, tk.END)
            return
        self.usuario = usuario
        self.destroy()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("JSConnect Win Coverage")
        self.geometry("540x360")
        self.resizable(False, False)
        self.conn = db.conectar()
        self.usuario = None
        self._build_ui()
        self.withdraw()
        self.after(0, self._pedir_login)

    def _build_ui(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        menu_sesion = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Sesion", menu=menu_sesion)
        menu_sesion.add_command(label="Cerrar sesion", command=self._cerrar_sesion)
        menu_sesion.add_separator()
        menu_sesion.add_command(label="Salir", command=self.destroy)

        main = ttk.Frame(self, padding=16)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="Coordenadas (latitud, longitud):").grid(row=0, column=0, sticky="w")
        self.txt_coordenadas = ttk.Entry(main, width=52)
        self.txt_coordenadas.grid(row=1, column=0, columnspan=2, sticky="we", pady=(2, 8))

        ttk.Label(main, text="DNI:").grid(row=2, column=0, sticky="w")
        self.txt_documento = ttk.Entry(main, width=32)
        self.txt_documento.grid(row=3, column=0, sticky="we", pady=(2, 2))

        self.btn_validar = ttk.Button(main, text="VALIDAR", command=self._validar)
        self.btn_validar.grid(row=4, column=0, columnspan=2, pady=10, sticky="we")

        frame_res = ttk.LabelFrame(main, text="Resultado", padding=10)
        frame_res.grid(row=5, column=0, columnspan=2, sticky="we")
        self.lbl_cobertura = ttk.Label(frame_res, text="Cobertura: —")
        self.lbl_cobertura.pack(anchor="w")
        self.lbl_score = ttk.Label(frame_res, text="Score: —")
        self.lbl_score.pack(anchor="w")

        self.lbl_estado = ttk.Label(main, text="Estado: sin sesion", anchor="w")
        self.lbl_estado.grid(row=6, column=0, columnspan=2, sticky="we", pady=(10, 0))

    def _pedir_login(self):
        dialog = LoginDialog(self, self.conn)
        self.wait_window(dialog)
        if dialog.usuario is None:
            self.destroy()
            return
        self.usuario = dialog.usuario
        self.lbl_estado.config(text=f"Sesion: {self.usuario['usuario']}")
        self.deiconify()

    def _cerrar_sesion(self):
        self.usuario = None
        self.txt_coordenadas.delete(0, tk.END)
        self.txt_documento.delete(0, tk.END)
        self.lbl_cobertura.config(text="Cobertura: —")
        self.lbl_score.config(text="Score: —")
        self.withdraw()
        self._pedir_login()

    def _validar(self):
        try:
            lat, lon = fields.parse_coordenadas(self.txt_coordenadas.get())
        except ValueError as exc:
            messagebox.showerror("Coordenadas", str(exc))
            return
        try:
            dni = fields.validar_dni(self.txt_documento.get())
        except ValueError as exc:
            messagebox.showerror("DNI", str(exc))
            return
        self._mostrar_resultado(db.validar(self.conn, lat, lon, dni))

    def _mostrar_resultado(self, resultado):
        cobertura = resultado["cobertura"]
        self.lbl_cobertura.config(
            text=f"Cobertura: {'SI' if cobertura['hay_cobertura'] else 'NO'}"
        )
        score = resultado.get("score")
        if score:
            texto = f"Score: {score['valor']} - {score.get('riesgo') or '?'}"
            if score.get("nombre"):
                texto += f" ({score['nombre']})"
            self.lbl_score.config(text=texto)
        else:
            self.lbl_score.config(text="Score: DNI no registrado")


def main():
    app = App()
    app.mainloop()
    return 0
