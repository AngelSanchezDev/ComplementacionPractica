"""Controlador del historial de consultas del usuario conectado."""

import sqlite3
from typing import Any

from validator_app.models import consultas


class HistorialController:
    def __init__(self, conn: sqlite3.Connection, usuario: dict[str, Any] | None):
        self.conn = conn
        self.usuario = usuario

    def listar(self, limite: int = 100) -> list[dict[str, Any]]:
        usuario_id = self.usuario["id"] if self.usuario else None
        return consultas.historial(self.conn, usuario_id, limite)
