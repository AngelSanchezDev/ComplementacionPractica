"""Controlador del explorador de clientes y su formulario (CRUD)."""

import sqlite3
from typing import Any

from validator_app.controllers import validaciones
from validator_app.models import clientes, riesgo
from validator_app.models.errors import APIError, ValidationError


class ClientesController:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def buscar(
        self, texto: str = "", riesgo_filtro: str | None = None, limite: int = 50, offset: int = 0
    ) -> tuple[list[dict[str, Any]], int]:
        return clientes.buscar_clientes(
            self.conn, texto, riesgo=riesgo_filtro, limite=limite, offset=offset
        )

    def obtener(self, dni: str) -> dict[str, Any] | None:
        return clientes.obtener_cliente(self.conn, dni)

    def existe(self, dni: str) -> bool:
        """No lanza: para el aviso de DNI duplicado en vivo mientras se escribe."""
        return len(dni) == 8 and clientes.existe_dni(self.conn, dni)

    def clasificar_preview(self, texto_score: str) -> dict[str, Any] | None:
        """No lanza: para la vista previa de riesgo en vivo. None si aun no es un score valido."""
        if not texto_score.isdigit():
            return None
        try:
            return riesgo.clasificar_score(self.conn, int(texto_score))
        except APIError:
            return None

    def crear(self, texto_dni: str, texto_nombre: str, texto_score: str) -> None:
        dni, nombre, score = self._validar_campos(texto_dni, texto_nombre, texto_score)
        clientes.crear_cliente(self.conn, dni, nombre, score)

    def actualizar(self, texto_dni: str, texto_nombre: str, texto_score: str) -> None:
        dni, nombre, score = self._validar_campos(texto_dni, texto_nombre, texto_score)
        clientes.actualizar_cliente(self.conn, dni, nombre, score)

    def eliminar(self, dni: str) -> None:
        clientes.eliminar_cliente(self.conn, dni)

    @staticmethod
    def _validar_campos(texto_dni: str, texto_nombre: str, texto_score: str):
        try:
            dni = validaciones.validar_dni(texto_dni)
            nombre = validaciones.validar_nombre(texto_nombre)
            score = validaciones.validar_score_texto(texto_score)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return dni, nombre, score
