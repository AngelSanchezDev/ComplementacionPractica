"""Controlador de la pantalla de inicio de sesion."""

import sqlite3
from typing import Any

from validator_app.models import usuarios
from validator_app.models.errors import LoginError


class LoginController:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def iniciar_sesion(self, usuario: str, password: str) -> dict[str, Any]:
        resultado = usuarios.autenticar(self.conn, usuario, password)
        if resultado is None:
            raise LoginError("Usuario o contraseña incorrectos.")
        return resultado
