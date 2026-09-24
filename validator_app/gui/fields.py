"""Validacion y parseo de entradas del usuario."""

import re


def parse_coordenadas(texto: str):
    """Convierte '-11.956037627741102, -77.04065381800075' en (lat, lon)."""
    partes = [p.strip() for p in texto.replace(";", ",").split(",")]
    if len(partes) != 2:
        raise ValueError("Formato esperado: latitud, longitud (separadas por coma)")
    try:
        lat, lon = float(partes[0]), float(partes[1])
    except ValueError:
        raise ValueError(
            "Las coordenadas deben ser numeros (ej: -11.956037627741102, -77.04065381800075)"
        ) from None
    if not -90 <= lat <= 90:
        raise ValueError("Latitud fuera de rango (-90 a 90)")
    if not -180 <= lon <= 180:
        raise ValueError("Longitud fuera de rango (-180 a 180)")
    return lat, lon


def validar_dni(numero: str) -> str:
    """Devuelve el DNI limpio si tiene exactamente 8 digitos."""
    n = numero.strip()
    if not re.fullmatch(r"\d{8}", n):
        raise ValueError("El DNI debe tener 8 digitos")
    return n
