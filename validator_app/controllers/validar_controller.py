"""Controlador de la pantalla de validar cobertura + score."""

import sqlite3
from typing import Any

from validator_app.controllers import validaciones
from validator_app.models import consultas
from validator_app.models.errors import ValidationError


class ValidarController:
    def __init__(self, conn: sqlite3.Connection, usuario: dict[str, Any] | None):
        self.conn = conn
        self.usuario = usuario

    def validar(self, texto_coordenadas: str, texto_dni: str) -> dict[str, Any]:
        try:
            lat, lon = validaciones.parse_coordenadas(texto_coordenadas)
            dni = validaciones.validar_dni(texto_dni)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        usuario_id = self.usuario["id"] if self.usuario else None
        return consultas.validar(self.conn, lat, lon, dni, usuario_id=usuario_id)
