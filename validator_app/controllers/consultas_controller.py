"""Controlador del catalogo de consultas SQL con distintos tipos de JOIN."""

import sqlite3
from typing import Any

from validator_app.models import consultas


class ConsultasController:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def catalogo(self) -> dict[str, dict[str, str]]:
        return consultas.CONSULTAS_CATALOGO

    def ejecutar(self, clave: str) -> tuple[list[str], list[tuple[Any, ...]]]:
        return consultas.ejecutar_consulta_catalogo(self.conn, clave)
