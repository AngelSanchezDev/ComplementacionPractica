"""Modelo: conexion, esquema completo y arranque de la base de datos SQLite.

Es el unico modulo que conoce a todas las entidades: orquesta la migracion,
la creacion de las 4 tablas y el sembrado de datos de ejemplo, en el orden
correcto (usuarios antes que consultas, por la clave foranea).
"""

from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

from validator_app.models import clientes, consultas, riesgo, usuarios

if getattr(sys, "frozen", False):
    _RAIZ = Path(sys.executable).resolve().parent
else:
    _RAIZ = Path(__file__).resolve().parents[2]
RUTA_BD_DEFECTO = _RAIZ / "datos" / "jsconnect.db"
VERSION_ESQUEMA = 2


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


def inicializar(conn: sqlite3.Connection) -> None:
    hay_migracion = clientes.preparar_migracion_v1(conn)

    conn.executescript(usuarios.ESQUEMA)
    conn.executescript(riesgo.ESQUEMA)
    conn.executescript(clientes.ESQUEMA)
    conn.executescript(consultas.ESQUEMA)

    if hay_migracion:
        clientes.completar_migracion_v1(conn)

    riesgo.sembrar_demo(conn)
    usuarios.sembrar_demo(conn)
    clientes.sembrar_demo(conn)

    conn.execute(f"PRAGMA user_version = {VERSION_ESQUEMA}")
