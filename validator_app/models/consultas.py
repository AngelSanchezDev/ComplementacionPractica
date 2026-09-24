"""Modelo: historial de validaciones y catalogo de consultas con distintos JOIN."""

from __future__ import annotations

import sqlite3
from typing import Any

from validator_app.models import clientes as clientes_modelo
from validator_app.models.errors import ValidationError

ESQUEMA = """
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


def validar(
    conn: sqlite3.Connection, lat: float, lon: float, dni: str, usuario_id: int | None = None
) -> dict[str, Any]:
    cobertura = clientes_modelo.validar_cobertura(lat, lon)
    score = clientes_modelo.validar_score(conn, dni) if cobertura["hay_cobertura"] else None
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


CONSULTAS_CATALOGO: dict[str, dict[str, str]] = {
    "clientes_riesgo": {
        "titulo": "Clientes con su nivel de riesgo",
        "tipo_join": "INNER JOIN",
        "descripcion": (
            "Cada cliente junto al rango de riesgo en el que cae su score. "
            "Al ser INNER JOIN, un cliente sin coincidencia en rangos_riesgo "
            "(no deberia pasar, pero en teoria podria) no apareceria."
        ),
        "sql": (
            "SELECT c.dni, c.nombre, c.score, r.riesgo\n"
            "FROM clientes c\n"
            "INNER JOIN rangos_riesgo r ON c.score BETWEEN r.score_min AND r.score_max\n"
            "ORDER BY c.score DESC\n"
            "LIMIT 200"
        ),
    },
    "riesgo_conteo": {
        "titulo": "Cuantos clientes hay por nivel de riesgo",
        "tipo_join": "LEFT JOIN",
        "descripcion": (
            "Parte de rangos_riesgo (5 filas fijas) y cuenta clientes. Con "
            "LEFT JOIN, un nivel de riesgo sin ningun cliente igual aparece, "
            "con total_clientes = 0; con INNER JOIN desaparaceria de la lista."
        ),
        "sql": (
            "SELECT r.riesgo, r.calificacion, COUNT(c.dni) AS total_clientes\n"
            "FROM rangos_riesgo r\n"
            "LEFT JOIN clientes c ON c.score BETWEEN r.score_min AND r.score_max\n"
            "GROUP BY r.id\n"
            "ORDER BY r.score_min"
        ),
    },
    "historial_completo": {
        "titulo": "Historial con nombre de cliente y de usuario",
        "tipo_join": "INNER JOIN multiple (3 tablas)",
        "descripcion": (
            "Une consultas con usuarios (quien la hizo) y con clientes (a "
            "quien se consulto). Al ser INNER JOIN en ambos casos, solo "
            "aparecen consultas con usuario valido y DNI que SI esta "
            "registrado en clientes."
        ),
        "sql": (
            "SELECT q.fecha, u.usuario, c.nombre AS cliente, q.dni, q.score\n"
            "FROM consultas q\n"
            "INNER JOIN usuarios u ON u.id = q.usuario_id\n"
            "INNER JOIN clientes c ON c.dni = q.dni\n"
            "ORDER BY q.id DESC\n"
            "LIMIT 200"
        ),
    },
    "nunca_consultados": {
        "titulo": "Clientes que nunca fueron consultados",
        "tipo_join": "LEFT JOIN (antijoin)",
        "descripcion": (
            "LEFT JOIN de clientes hacia consultas, quedandose solo con las "
            "filas donde no hubo coincidencia (q.id IS NULL). Es la forma "
            "clasica de responder 'que hay en A que no esta en B'."
        ),
        "sql": (
            "SELECT c.dni, c.nombre, c.score\n"
            "FROM clientes c\n"
            "LEFT JOIN consultas q ON q.dni = c.dni\n"
            "WHERE q.id IS NULL\n"
            "ORDER BY c.nombre\n"
            "LIMIT 200"
        ),
    },
    "promedio_por_riesgo": {
        "titulo": "Score promedio por nivel de riesgo",
        "tipo_join": "INNER JOIN + agregacion",
        "descripcion": (
            "Igual patron que el dashboard, pero con AVG en vez de COUNT: "
            "agrupa los clientes por su rango de riesgo y calcula el "
            "promedio de su score."
        ),
        "sql": (
            "SELECT r.riesgo, COUNT(*) AS clientes, ROUND(AVG(c.score), 1) AS score_promedio\n"
            "FROM clientes c\n"
            "INNER JOIN rangos_riesgo r ON c.score BETWEEN r.score_min AND r.score_max\n"
            "GROUP BY r.id\n"
            "ORDER BY r.score_min"
        ),
    },
}


def ejecutar_consulta_catalogo(
    conn: sqlite3.Connection, clave: str
) -> tuple[list[str], list[tuple[Any, ...]]]:
    """Ejecuta una consulta del catalogo y devuelve (columnas, filas)."""
    entrada = CONSULTAS_CATALOGO.get(clave)
    if entrada is None:
        raise ValidationError(f"Consulta '{clave}' no existe en el catalogo.")
    cursor = conn.execute(entrada["sql"])
    columnas = [d[0] for d in cursor.description]
    filas = cursor.fetchall()
    return columnas, [tuple(fila) for fila in filas]
