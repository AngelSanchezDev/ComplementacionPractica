import importlib.util
from pathlib import Path

from validator_app.core import db

_RUTA = Path(__file__).resolve().parents[1] / "tools" / "seed.py"
_spec = importlib.util.spec_from_file_location("seed", _RUTA)
seed = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(seed)


def test_seed_agrega_usuario_y_cliente(tmp_path, monkeypatch):
    ruta = tmp_path / "seed.db"
    monkeypatch.setenv("JSCONNECT_DB", str(ruta))

    assert seed.main(["usuario", "profe", "clave123", "Profesor"]) == 0
    assert seed.main(["cliente", "11223344", "720", "BAJO", "Prueba"]) == 0

    conn = db.conectar(ruta)
    assert db.autenticar(conn, "profe", "clave123") is not None
    assert db.validar_score(conn, "11223344")["valor"] == 720
    conn.close()


def test_seed_usuario_duplicado_falla(tmp_path, monkeypatch):
    monkeypatch.setenv("JSCONNECT_DB", str(tmp_path / "seed.db"))
    assert seed.main(["usuario", "admin", "x"]) == 1
