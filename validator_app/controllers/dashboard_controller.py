"""Controlador del dashboard de clientes por nivel de riesgo."""

import sqlite3
from typing import Any

from validator_app.models import riesgo


class DashboardController:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def resumen(self) -> list[dict[str, Any]]:
        return riesgo.resumen_por_riesgo(self.conn)
