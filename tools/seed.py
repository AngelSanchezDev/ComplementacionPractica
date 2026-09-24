"""Agrega usuarios o clientes a la base de datos local.

Uso:
    python tools/seed.py usuario <usuario> <password> [nombre]
    python tools/seed.py cliente <dni> <score> <nombre>
    python tools/seed.py generar <cantidad>
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from validator_app.models import clientes, database, usuarios
from validator_app.models.errors import APIError


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Carga datos en la BD local.")
    sub = parser.add_subparsers(dest="comando", required=True)

    p_usuario = sub.add_parser("usuario", help="Crear un usuario")
    p_usuario.add_argument("usuario")
    p_usuario.add_argument("password")
    p_usuario.add_argument("nombre", nargs="?", default="")

    p_cliente = sub.add_parser("cliente", help="Registrar un cliente nuevo (DNI no repetido)")
    p_cliente.add_argument("dni")
    p_cliente.add_argument("score", type=int)
    p_cliente.add_argument("nombre")

    p_generar = sub.add_parser("generar", help="Generar clientes ficticios adicionales")
    p_generar.add_argument("cantidad", type=int)
    p_generar.add_argument("--semilla", type=int, default=42)

    args = parser.parse_args(argv)
    conn = database.conectar()
    try:
        if args.comando == "usuario":
            usuarios.crear_usuario(conn, args.usuario, args.password, args.nombre)
            print(f"Usuario '{args.usuario}' creado.")
        elif args.comando == "cliente":
            clientes.crear_cliente(conn, args.dni, args.nombre, args.score)
            print(f"Cliente {args.dni} registrado con score {args.score}.")
        else:
            creados = clientes.generar_clientes(conn, args.cantidad, semilla=args.semilla)
            print(f"{creados} clientes generados.")
    except APIError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
