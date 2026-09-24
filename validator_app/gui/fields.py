"""Validacion y parseo de entradas del usuario."""

import re
from collections.abc import Callable


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


def validar_score_texto(texto: str) -> int:
    """Convierte el texto del score a entero entre 0 y 1000."""
    t = texto.strip()
    if not t.isdigit():
        raise ValueError("El score debe ser un numero")
    valor = int(t)
    if not 0 <= valor <= 1000:
        raise ValueError("El score debe estar entre 0 y 1000")
    return valor


def validar_nombre(texto: str) -> str:
    """Nombre con solo letras y espacios, minimo 3 caracteres."""
    nombre = " ".join(texto.split())
    if len(nombre) < 3:
        raise ValueError("El nombre debe tener al menos 3 caracteres")
    if not re.fullmatch(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ ]+", nombre):
        raise ValueError("El nombre solo puede tener letras y espacios")
    return nombre


def permitir_digitos(max_len: int) -> Callable[[str], bool]:
    """Filtro para validatecommand de Tk: solo digitos y hasta max_len caracteres."""

    def filtro(propuesto: str) -> bool:
        return propuesto == "" or (propuesto.isdigit() and len(propuesto) <= max_len)

    return filtro
