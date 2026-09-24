"""Modelo: tabla de rangos de riesgo y su clasificacion por score."""

from __future__ import annotations

import sqlite3
from typing import Any

from validator_app.models.errors import ScoreError, ValidationError

SCORE_MIN = 0
SCORE_MAX = 1000

RANGOS_RIESGO = [
    (0, 299, "Muy Alto", "Malo", "#e5484d"),
    (300, 549, "Alto", "Regular", "#f76b15"),
    (550, 749, "Medio", "Bueno", "#e2a336"),
    (750, 899, "Bajo", "Muy Bueno", "#30a46c"),
    (900, 1000, "Muy Bajo", "Excelente", "#1f7a4d"),
]

ESQUEMA = """
CREATE TABLE IF NOT EXISTS rangos_riesgo (
    id INTEGER PRIMARY KEY,
    score_min INTEGER NOT NULL,
    score_max INTEGER NOT NULL,
    riesgo TEXT UNIQUE NOT NULL,
    calificacion TEXT NOT NULL,
    color TEXT NOT NULL,
    CHECK (score_min <= score_max)
);
"""


def validar_score(score: Any) -> int:
    if isinstance(score, bool) or not isinstance(score, int):
        raise ValidationError("El score debe ser un numero entero.")
    if not SCORE_MIN <= score <= SCORE_MAX:
        raise ValidationError(f"El score debe estar entre {SCORE_MIN} y {SCORE_MAX}.")
    return score


def rangos_riesgo(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    filas = conn.execute(
        "SELECT score_min, score_max, riesgo, calificacion, color FROM rangos_riesgo "
        "ORDER BY score_min"
    ).fetchall()
    return [dict(fila) for fila in filas]


def clasificar_score(conn: sqlite3.Connection, score: int) -> dict[str, Any]:
    validar_score(score)
    fila = conn.execute(
        "SELECT riesgo, calificacion, color FROM rangos_riesgo "
        "WHERE ? BETWEEN score_min AND score_max",
        (score,),
    ).fetchone()
    if fila is None:
        raise ScoreError(f"No hay un rango de riesgo para el score {score}.")
    return dict(fila)


def resumen_por_riesgo(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Cuenta clientes por nivel de riesgo (LEFT JOIN: incluye niveles con 0 clientes)."""
    filas = conn.execute(
        "SELECT r.riesgo, r.calificacion, r.color, COUNT(c.dni) AS total "
        "FROM rangos_riesgo r "
        "LEFT JOIN clientes c ON c.score BETWEEN r.score_min AND r.score_max "
        "GROUP BY r.id ORDER BY r.score_min"
    ).fetchall()
    return [dict(fila) for fila in filas]


def sembrar_demo(conn: sqlite3.Connection) -> None:
    if conn.execute("SELECT COUNT(*) FROM rangos_riesgo").fetchone()[0] == 0:
        with conn:
            conn.executemany(
                "INSERT INTO rangos_riesgo (score_min, score_max, riesgo, calificacion, color) "
                "VALUES (?, ?, ?, ?, ?)",
                RANGOS_RIESGO,
            )
