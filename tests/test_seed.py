import importlib.util
from pathlib import Path

from validator_app.models import clientes, database, usuarios

_RUTA = Path(__file__).resolve().parents[1] / "tools" / "seed.py"
_spec = importlib.util.spec_from_file_location("seed", _RUTA)
seed = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(seed)


def test_seed_agrega_usuario_y_cliente(tmp_path, monkeypatch):
    ruta = tmp_path / "seed.db"
    monkeypatch.setenv("JSCONNECT_DB", str(ruta))
    monkeypatch.setattr(clientes, "CANTIDAD_DEMO", 20)

    assert seed.main(["usuario", "profe", "clave123", "Profesor"]) == 0
    assert seed.main(["cliente", "11223344", "720", "Cliente de Prueba"]) == 0

    conn = database.conectar(ruta)
    assert usuarios.autenticar(conn, "profe", "clave123") is not None
    assert clientes.validar_score(conn, "11223344")["valor"] == 720
    conn.close()


def test_seed_usuario_duplicado_falla(tmp_path, monkeypatch):
    monkeypatch.setenv("JSCONNECT_DB", str(tmp_path / "seed.db"))
    monkeypatch.setattr(clientes, "CANTIDAD_DEMO", 20)
    assert seed.main(["usuario", "admin", "x"]) == 1


def test_seed_cliente_duplicado_falla(tmp_path, monkeypatch):
    monkeypatch.setenv("JSCONNECT_DB", str(tmp_path / "seed2.db"))
    monkeypatch.setattr(clientes, "CANTIDAD_DEMO", 20)
    seed.main(["cliente", "11223344", "720", "Cliente Uno"])
    assert seed.main(["cliente", "11223344", "500", "Cliente Dos"]) == 1


def test_seed_generar(tmp_path, monkeypatch):
    monkeypatch.setenv("JSCONNECT_DB", str(tmp_path / "seed3.db"))
    monkeypatch.setattr(clientes, "CANTIDAD_DEMO", 0)
    antes = database.conectar(tmp_path / "seed3.db")
    total_antes = clientes.contar_clientes(antes)
    antes.close()

    assert seed.main(["generar", "50"]) == 0

    conn = database.conectar(tmp_path / "seed3.db")
    assert clientes.contar_clientes(conn) == total_antes + 50
    conn.close()
