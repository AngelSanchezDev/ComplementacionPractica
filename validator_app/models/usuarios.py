"""Modelo: usuarios que pueden iniciar sesion en la aplicacion."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
from typing import Any

from validator_app.models.errors import ValidationError

ITERACIONES = 100_000

USUARIOS_DEMO = [("admin", "admin123", "Administrador")]

ESQUEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY,
    usuario TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    nombre TEXT
);
"""


def _hash(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt), ITERACIONES
    ).hex()


def crear_usuario(
    conn: sqlite3.Connection, usuario: str, password: str, nombre: str = ""
) -> None:
    usuario = usuario.strip()
    if not usuario or not password:
        raise ValidationError("Usuario y contraseña son obligatorios.")
    salt = secrets.token_hex(16)
    try:
        with conn:
            conn.execute(
                "INSERT INTO usuarios (usuario, password_hash, salt, nombre) VALUES (?, ?, ?, ?)",
                (usuario, _hash(password, salt), salt, nombre),
            )
    except sqlite3.IntegrityError:
        raise ValidationError(f"El usuario '{usuario}' ya existe.") from None


def autenticar(conn: sqlite3.Connection, usuario: str, password: str) -> dict[str, Any] | None:
    fila = conn.execute(
        "SELECT id, usuario, password_hash, salt, nombre FROM usuarios WHERE usuario = ?",
        (usuario.strip(),),
    ).fetchone()
    if fila is None:
        return None
    if not hmac.compare_digest(fila["password_hash"], _hash(password, fila["salt"])):
        return None
    return {"id": fila["id"], "usuario": fila["usuario"], "nombre": fila["nombre"]}


def sembrar_demo(conn: sqlite3.Connection) -> None:
    if conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
        for usuario, password, nombre in USUARIOS_DEMO:
            crear_usuario(conn, usuario, password, nombre)
