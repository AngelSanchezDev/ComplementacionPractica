"""Base de datos local (SQLite): usuarios, clientes, rangos de riesgo y consultas."""

from __future__ import annotations

import hashlib
import hmac
import os
import random
import re
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
VERSION_ESQUEMA = 2
CANTIDAD_DEMO = 1_000
SCORE_MIN = 0
SCORE_MAX = 1000

RANGOS_RIESGO = [
    (0, 299, "Muy Alto", "Malo", "#e5484d"),
    (300, 549, "Alto", "Regular", "#f76b15"),
    (550, 749, "Medio", "Bueno", "#e2a336"),
    (750, 899, "Bajo", "Muy Bueno", "#30a46c"),
    (900, 1000, "Muy Bajo", "Excelente", "#1f7a4d"),
]

USUARIOS_DEMO = [("admin", "admin123", "Administrador")]
CLIENTES_DEMO = [
    ("12345678", "Juan Perez Gomez", 720),
    ("87654321", "Maria Lopez Diaz", 580),
    ("11111111", "Carlos Ramos Vega", 250),
    ("22222222", "Ana Torres Rojas", 910),
    ("33333333", "Luis Quispe Mamani", 480),
]

NOMBRES = [
    "Juan", "Jose", "Luis", "Carlos", "Jorge", "Miguel", "Pedro", "Ricardo", "Diego",
    "Javier", "Fernando", "Alberto", "Victor", "Raul", "Cesar", "Daniel", "Manuel",
    "Andres", "Sergio", "Hugo", "Maria", "Rosa", "Ana", "Carmen", "Lucia", "Patricia",
    "Julia", "Elena", "Sofia", "Valeria", "Camila", "Gabriela", "Andrea", "Milagros",
    "Fiorella", "Diana", "Claudia", "Karina", "Veronica", "Silvia",
]
APELLIDOS = [
    "Quispe", "Flores", "Sanchez", "Rodriguez", "Garcia", "Mamani", "Huaman", "Rojas",
    "Chavez", "Vasquez", "Ramirez", "Torres", "Mendoza", "Castillo", "Gutierrez",
    "Diaz", "Lopez", "Perez", "Espinoza", "Ramos", "Vargas", "Gonzales", "Cruz",
    "Condori", "Salazar", "Reyes", "Romero", "Morales", "Herrera", "Vega", "Silva",
    "Ccori", "Palomino", "Cardenas", "Paredes", "Aguilar", "Medina", "Castro",
    "Ortiz", "Navarro",
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
    conn.execute("PRAGMA foreign_keys = ON")
    inicializar(conn)
    return conn


_ESQUEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY,
    usuario TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    nombre TEXT
);
CREATE TABLE IF NOT EXISTS rangos_riesgo (
    id INTEGER PRIMARY KEY,
    score_min INTEGER NOT NULL,
    score_max INTEGER NOT NULL,
    riesgo TEXT UNIQUE NOT NULL,
    calificacion TEXT NOT NULL,
    color TEXT NOT NULL,
    CHECK (score_min <= score_max)
);
CREATE TABLE IF NOT EXISTS clientes (
    dni TEXT PRIMARY KEY CHECK (length(dni) = 8 AND dni NOT GLOB '*[^0-9]*'),
    nombre TEXT NOT NULL,
    score INTEGER NOT NULL CHECK (score BETWEEN 0 AND 1000)
);
CREATE INDEX IF NOT EXISTS idx_clientes_nombre ON clientes (nombre);
CREATE TABLE IF NOT EXISTS consultas (
    id INTEGER PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios (id) ON DELETE SET NULL,
    dni TEXT NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    cobertura TEXT NOT NULL,
    score INTEGER,
    fecha TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
"""


def inicializar(conn: sqlite3.Connection) -> None:
    _migrar_v1(conn)
    conn.executescript(_ESQUEMA)
    if conn.execute("SELECT COUNT(*) FROM rangos_riesgo").fetchone()[0] == 0:
        with conn:
            conn.executemany(
                "INSERT INTO rangos_riesgo (score_min, score_max, riesgo, calificacion, color) "
                "VALUES (?, ?, ?, ?, ?)",
                RANGOS_RIESGO,
            )
    if conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
        for usuario, password, nombre in USUARIOS_DEMO:
            crear_usuario(conn, usuario, password, nombre)
    if conn.execute("SELECT COUNT(*) FROM clientes").fetchone()[0] == 0:
        with conn:
            conn.executemany(
                "INSERT INTO clientes (dni, nombre, score) VALUES (?, ?, ?)", CLIENTES_DEMO
            )
    faltan = CANTIDAD_DEMO - contar_clientes(conn)
    if faltan > 0:
        generar_clientes(conn, faltan)
    conn.execute(f"PRAGMA user_version = {VERSION_ESQUEMA}")


def _migrar_v1(conn: sqlite3.Connection) -> None:
    """Convierte la tabla clientes v1 (con columna riesgo manual) al esquema v2."""
    columnas = {fila[1] for fila in conn.execute("PRAGMA table_info(clientes)")}
    if "riesgo" not in columnas:
        return
    with conn:
        conn.execute("ALTER TABLE clientes RENAME TO clientes_v1")
        conn.executescript(_ESQUEMA)
        conn.execute(
            "INSERT OR IGNORE INTO clientes (dni, nombre, score) "
            "SELECT dni, COALESCE(NULLIF(trim(nombre), ''), 'Sin nombre'), "
            "MIN(MAX(score, 0), 1000) FROM clientes_v1"
        )
        conn.execute("DROP TABLE clientes_v1")


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


def rangos_riesgo(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    filas = conn.execute(
        "SELECT score_min, score_max, riesgo, calificacion, color FROM rangos_riesgo "
        "ORDER BY score_min"
    ).fetchall()
    return [dict(fila) for fila in filas]


def clasificar_score(conn: sqlite3.Connection, score: int) -> dict[str, Any]:
    _validar_score(score)
    fila = conn.execute(
        "SELECT riesgo, calificacion, color FROM rangos_riesgo "
        "WHERE ? BETWEEN score_min AND score_max",
        (score,),
    ).fetchone()
    if fila is None:
        raise ScoreError(f"No hay un rango de riesgo para el score {score}.")
    return dict(fila)


def _validar_dni(dni: str) -> str:
    dni = str(dni).strip()
    if not re.fullmatch(r"\d{8}", dni):
        raise ValidationError("El DNI debe tener exactamente 8 digitos numericos.")
    return dni


def _validar_nombre(nombre: str) -> str:
    nombre = " ".join(str(nombre).split())
    if len(nombre) < 3:
        raise ValidationError("El nombre debe tener al menos 3 caracteres.")
    return nombre


def _validar_score(score: Any) -> int:
    if isinstance(score, bool) or not isinstance(score, int):
        raise ValidationError("El score debe ser un numero entero.")
    if not SCORE_MIN <= score <= SCORE_MAX:
        raise ValidationError(f"El score debe estar entre {SCORE_MIN} y {SCORE_MAX}.")
    return score


def contar_clientes(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]


def existe_dni(conn: sqlite3.Connection, dni: str) -> bool:
    return conn.execute("SELECT 1 FROM clientes WHERE dni = ?", (dni,)).fetchone() is not None


_SELECT_CLIENTE = (
    "SELECT c.dni, c.nombre, c.score, r.riesgo, r.calificacion, r.color "
    "FROM clientes c LEFT JOIN rangos_riesgo r "
    "ON c.score BETWEEN r.score_min AND r.score_max"
)


def obtener_cliente(conn: sqlite3.Connection, dni: str) -> dict[str, Any] | None:
    fila = conn.execute(f"{_SELECT_CLIENTE} WHERE c.dni = ?", (dni,)).fetchone()
    return dict(fila) if fila else None


def crear_cliente(conn: sqlite3.Connection, dni: str, nombre: str, score: int) -> None:
    dni, nombre, score = _validar_dni(dni), _validar_nombre(nombre), _validar_score(score)
    if existe_dni(conn, dni):
        raise ValidationError(f"El DNI {dni} ya esta registrado.", "ERR_DNI_DUPLICADO")
    with conn:
        conn.execute(
            "INSERT INTO clientes (dni, nombre, score) VALUES (?, ?, ?)", (dni, nombre, score)
        )


def actualizar_cliente(conn: sqlite3.Connection, dni: str, nombre: str, score: int) -> None:
    dni, nombre, score = _validar_dni(dni), _validar_nombre(nombre), _validar_score(score)
    with conn:
        cursor = conn.execute(
            "UPDATE clientes SET nombre = ?, score = ? WHERE dni = ?", (nombre, score, dni)
        )
    if cursor.rowcount == 0:
        raise ValidationError(f"El DNI {dni} no esta registrado.", "ERR_DNI_NO_EXISTE")


def eliminar_cliente(conn: sqlite3.Connection, dni: str) -> None:
    with conn:
        cursor = conn.execute("DELETE FROM clientes WHERE dni = ?", (dni,))
    if cursor.rowcount == 0:
        raise ValidationError(f"El DNI {dni} no esta registrado.", "ERR_DNI_NO_EXISTE")


def buscar_clientes(
    conn: sqlite3.Connection, texto: str = "", limite: int = 50, offset: int = 0
) -> tuple[list[dict[str, Any]], int]:
    texto = texto.strip()
    if not texto:
        filtro, params = "", ()
    elif texto.isdigit():
        filtro, params = " WHERE c.dni LIKE ?", (f"{texto}%",)
    else:
        filtro, params = " WHERE c.nombre LIKE ?", (f"%{texto}%",)
    total = conn.execute(f"SELECT COUNT(*) FROM clientes c{filtro}", params).fetchone()[0]
    filas = conn.execute(
        f"{_SELECT_CLIENTE}{filtro} ORDER BY c.nombre LIMIT ? OFFSET ?",
        (*params, limite, offset),
    ).fetchall()
    return [dict(fila) for fila in filas], total


def generar_clientes(conn: sqlite3.Connection, cantidad: int, semilla: int = 42) -> int:
    """Inserta `cantidad` clientes ficticios (deterministas por semilla). Devuelve cuantos."""
    rnd = random.Random(semilla)
    existentes = {fila[0] for fila in conn.execute("SELECT dni FROM clientes")}
    nuevos = []
    while len(nuevos) < cantidad:
        dni = f"{rnd.randint(10_000_000, 79_999_999)}"
        if dni in existentes:
            continue
        existentes.add(dni)
        score_min, score_max = rnd.choice(RANGOS_RIESGO)[:2]
        nombre = f"{rnd.choice(NOMBRES)} {rnd.choice(APELLIDOS)} {rnd.choice(APELLIDOS)}"
        nuevos.append((dni, nombre, rnd.randint(score_min, score_max)))
    with conn:
        conn.executemany("INSERT INTO clientes (dni, nombre, score) VALUES (?, ?, ?)", nuevos)
    return len(nuevos)


def validar_cobertura(lat: float, lon: float) -> dict[str, Any]:
    """Cobertura simulada: siempre hay cobertura."""
    return {"hay_cobertura": True, "cobertura": "SI", "tipo": "SIMULADA"}


def validar_score(conn: sqlite3.Connection, dni: str) -> dict[str, Any] | None:
    cliente = obtener_cliente(conn, dni)
    if cliente is None:
        return None
    return {
        "valor": cliente["score"],
        "riesgo": cliente["riesgo"],
        "calificacion": cliente["calificacion"],
        "color": cliente["color"],
        "nombre": cliente["nombre"],
        "documento": cliente["dni"],
        "valido": True,
    }


def validar(
    conn: sqlite3.Connection, lat: float, lon: float, dni: str, usuario_id: int | None = None
) -> dict[str, Any]:
    cobertura = validar_cobertura(lat, lon)
    score = validar_score(conn, dni) if cobertura["hay_cobertura"] else None
    with conn:
        conn.execute(
            "INSERT INTO consultas (usuario_id, dni, lat, lon, cobertura, score) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (usuario_id, dni, lat, lon, cobertura["cobertura"], score["valor"] if score else None),
        )
    return {"cobertura": cobertura, "score": score}


def historial(
    conn: sqlite3.Connection, usuario_id: int | None, limite: int = 100
) -> list[dict[str, Any]]:
    filas = conn.execute(
        "SELECT q.fecha, q.dni, q.cobertura, q.score, r.riesgo, r.calificacion "
        "FROM consultas q LEFT JOIN rangos_riesgo r "
        "ON q.score BETWEEN r.score_min AND r.score_max "
        "WHERE q.usuario_id IS ? ORDER BY q.id DESC LIMIT ?",
        (usuario_id, limite),
    ).fetchall()
    return [dict(fila) for fila in filas]
