"""Vista: filtros de entrada de teclado para widgets de Tk (sin logica de negocio)."""

from collections.abc import Callable


def permitir_digitos(max_len: int) -> Callable[[str], bool]:
    """Filtro para validatecommand de Tk: solo digitos y hasta max_len caracteres."""

    def filtro(propuesto: str) -> bool:
        return propuesto == "" or (propuesto.isdigit() and len(propuesto) <= max_len)

    return filtro
