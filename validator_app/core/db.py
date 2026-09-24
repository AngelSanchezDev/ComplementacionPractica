"""Base de datos local (SQLite): usuarios, clientes y validaciones."""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import sqlite3
import sys
from pathlib import Path
from typing import Any

if getattr(sys, "frozen", False):
    _RAIZ = Path(sys.executable).resolve().parent
else:
    _RAIZ = Path(__file__).resolve().parents[2]
RUTA_BD_DEFECTO = _RAIZ / "datos" / "jsconnect.db"
ITERACIONES = 100_000

USUARIOS_DEMO = [("admin", "admin123", "Administrador")]
CLIENTES_DEMO = [
    ("12345678", "Juan Perez", 720, "BAJO"),
    ("87654321", "Maria Lopez", 580, "MEDIO"),
    ("11111111", "Carlos Ramos", 423, "MUY ALTO"),
    ("22222222", "Ana Torres", 650, "BAJO"),
    ("33333333", "Luis Quispe", 480, "ALTO"),
]


class APIError(Exception):
    def __init__(self, message: str, code: str = "ERR_UNKNOWN"):
        super().__init__(message)
        self.code = code


class LoginError(APIError):
    def __init__(self, message: str, code: str = "ERR_LOGIN"):
        super().__init__(message, code)


class ScoreError(APIError):
    def __init__(self, message: str, code: str = "ERR_SCORE"):
        super().__init__(message, code)


class ValidationError(APIError):
    def __init__(self, message: str, code: str = "ERR_VALIDATION"):
        super().__init__(message, code)


def ruta_bd() -> Path:
    return Path(os.environ.get("JSCONNECT_DB") or RUTA_BD_DEFECTO)


def conectar(ruta: str | Path | None = None) -> sqlite3.Connection:
    ruta = Path(ruta) if ruta else ruta_bd()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(ruta)
    conn.row_factory = sqlite3.Row
    inicializar(conn)
    return conn


def inicializar(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY,
            usuario TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            nombre TEXT
        );
        CREATE TABLE IF NOT EXISTS clientes (
            dni TEXT PRIMARY KEY CHECK (length(dni) = 8),
            nombre TEXT,
            score INTEGER NOT NULL,
            riesgo TEXT
        );
        """
    )
    if conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
        for usuario, password, nombre in USUARIOS_DEMO:
            crear_usuario(conn, usuario, password, nombre)
    if conn.execute("SELECT COUNT(*) FROM clientes").fetchone()[0] == 0:
        for dni, nombre, score, riesgo in CLIENTES_DEMO:
            registrar_cliente(conn, dni, nombre, score, riesgo)


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


def registrar_cliente(
    conn: sqlite3.Connection, dni: str, nombre: str, score: int, riesgo: str = ""
) -> None:
    if not (len(dni) == 8 and dni.isdigit()):
        raise ValidationError("El DNI debe tener 8 digitos.")
    with conn:
        conn.execute(
            "INSERT INTO clientes (dni, nombre, score, riesgo) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(dni) DO UPDATE SET nombre = excluded.nombre, "
            "score = excluded.score, riesgo = excluded.riesgo",
            (dni, nombre, int(score), riesgo),
        )


def validar_cobertura(lat: float, lon: float) -> dict[str, Any]:
    """Cobertura simulada: siempre hay cobertura."""
    return {"hay_cobertura": True, "cobertura": "SI", "tipo": "SIMULADA"}


def validar_score(conn: sqlite3.Connection, dni: str) -> dict[str, Any] | None:
    fila = conn.execute(
        "SELECT dni, nombre, score, riesgo FROM clientes WHERE dni = ?", (dni,)
    ).fetchone()
    if fila is None:
        return None
    return {
        "valor": fila["score"],
        "riesgo": fila["riesgo"],
        "nombre": fila["nombre"],
        "documento": fila["dni"],
        "valido": True,
    }


def validar(conn: sqlite3.Connection, lat: float, lon: float, dni: str) -> dict[str, Any]:
    cobertura = validar_cobertura(lat, lon)
    score = validar_score(conn, dni) if cobertura["hay_cobertura"] else None
    return {"cobertura": cobertura, "score": score}
