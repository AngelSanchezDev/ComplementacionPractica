"""Modelo: clientes consultables por DNI (CRUD, busqueda, datos de prueba)."""

from __future__ import annotations

import random
import re
import sqlite3
from typing import Any

from validator_app.models import riesgo as riesgo_modelo
from validator_app.models.errors import ValidationError
from validator_app.models.riesgo import RANGOS_RIESGO

CANTIDAD_DEMO = 1_000

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

ESQUEMA = """
CREATE TABLE IF NOT EXISTS clientes (
    dni TEXT PRIMARY KEY CHECK (length(dni) = 8 AND dni NOT GLOB '*[^0-9]*'),
    nombre TEXT NOT NULL,
    score INTEGER NOT NULL CHECK (score BETWEEN 0 AND 1000)
);
CREATE INDEX IF NOT EXISTS idx_clientes_nombre ON clientes (nombre);
"""

_SELECT_CLIENTE = (
    "SELECT c.dni, c.nombre, c.score, r.riesgo, r.calificacion, r.color "
    "FROM clientes c LEFT JOIN rangos_riesgo r "
    "ON c.score BETWEEN r.score_min AND r.score_max"
)


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


def contar_clientes(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]


def existe_dni(conn: sqlite3.Connection, dni: str) -> bool:
    return conn.execute("SELECT 1 FROM clientes WHERE dni = ?", (dni,)).fetchone() is not None


def obtener_cliente(conn: sqlite3.Connection, dni: str) -> dict[str, Any] | None:
    fila = conn.execute(f"{_SELECT_CLIENTE} WHERE c.dni = ?", (dni,)).fetchone()
    return dict(fila) if fila else None


def crear_cliente(conn: sqlite3.Connection, dni: str, nombre: str, score: int) -> None:
    dni, nombre, score = (
        _validar_dni(dni), _validar_nombre(nombre), riesgo_modelo.validar_score(score),
    )
    if existe_dni(conn, dni):
        raise ValidationError(f"El DNI {dni} ya esta registrado.", "ERR_DNI_DUPLICADO")
    with conn:
        conn.execute(
            "INSERT INTO clientes (dni, nombre, score) VALUES (?, ?, ?)", (dni, nombre, score)
        )


def actualizar_cliente(conn: sqlite3.Connection, dni: str, nombre: str, score: int) -> None:
    dni, nombre, score = (
        _validar_dni(dni), _validar_nombre(nombre), riesgo_modelo.validar_score(score),
    )
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
    conn: sqlite3.Connection,
    texto: str = "",
    riesgo: str | None = None,
    limite: int = 50,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    texto = texto.strip()
    condiciones: list[str] = []
    params: list[Any] = []
    if texto.isdigit():
        condiciones.append("c.dni LIKE ?")
        params.append(f"{texto}%")
    elif texto:
        condiciones.append("c.nombre LIKE ?")
        params.append(f"%{texto}%")
    if riesgo:
        condiciones.append("r.riesgo = ?")
        params.append(riesgo)
    filtro = f" WHERE {' AND '.join(condiciones)}" if condiciones else ""
    total = conn.execute(
        f"SELECT COUNT(*) FROM clientes c "
        f"LEFT JOIN rangos_riesgo r ON c.score BETWEEN r.score_min AND r.score_max{filtro}",
        params,
    ).fetchone()[0]
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


def preparar_migracion_v1(conn: sqlite3.Connection) -> bool:
    """Si detecta el esquema viejo (con columna `riesgo`), renombra la tabla
    para poder recrearla despues con el esquema nuevo. Devuelve True si hacia
    falta migrar."""
    columnas = {fila[1] for fila in conn.execute("PRAGMA table_info(clientes)")}
    if "riesgo" not in columnas:
        return False
    with conn:
        conn.execute("ALTER TABLE clientes RENAME TO clientes_v1")
    return True


def completar_migracion_v1(conn: sqlite3.Connection) -> None:
    """Copia los datos de la tabla vieja (ya renombrada) a la nueva y la borra."""
    with conn:
        conn.execute(
            "INSERT OR IGNORE INTO clientes (dni, nombre, score) "
            "SELECT dni, COALESCE(NULLIF(trim(nombre), ''), 'Sin nombre'), "
            "MIN(MAX(score, 0), 1000) FROM clientes_v1"
        )
        conn.execute("DROP TABLE clientes_v1")


def sembrar_demo(conn: sqlite3.Connection) -> None:
    if conn.execute("SELECT COUNT(*) FROM clientes").fetchone()[0] == 0:
        with conn:
            conn.executemany(
                "INSERT INTO clientes (dni, nombre, score) VALUES (?, ?, ?)", CLIENTES_DEMO
            )
    faltan = CANTIDAD_DEMO - contar_clientes(conn)
    if faltan > 0:
        generar_clientes(conn, faltan)
