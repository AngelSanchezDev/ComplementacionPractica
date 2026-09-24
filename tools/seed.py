"""Agrega usuarios o clientes a la base de datos local.

Uso:
    python tools/seed.py usuario <usuario> <password> [nombre]
    python tools/seed.py cliente <dni> <score> [riesgo] [nombre]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from validator_app.core import db


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Carga datos en la BD local.")
    sub = parser.add_subparsers(dest="comando", required=True)

    p_usuario = sub.add_parser("usuario", help="Crear un usuario")
    p_usuario.add_argument("usuario")
    p_usuario.add_argument("password")
    p_usuario.add_argument("nombre", nargs="?", default="")

    p_cliente = sub.add_parser("cliente", help="Registrar o actualizar el score de un DNI")
    p_cliente.add_argument("dni")
    p_cliente.add_argument("score", type=int)
    p_cliente.add_argument("riesgo", nargs="?", default="")
    p_cliente.add_argument("nombre", nargs="?", default="")

    args = parser.parse_args(argv)
    conn = db.conectar()
    try:
        if args.comando == "usuario":
            db.crear_usuario(conn, args.usuario, args.password, args.nombre)
            print(f"Usuario '{args.usuario}' creado.")
        else:
            db.registrar_cliente(conn, args.dni, args.nombre, args.score, args.riesgo)
            print(f"Cliente {args.dni} registrado con score {args.score}.")
    except db.APIError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
