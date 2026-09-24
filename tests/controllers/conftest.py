import pytest

from validator_app.models import clientes, database


@pytest.fixture
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(clientes, "CANTIDAD_DEMO", 20)
    conexion = database.conectar(tmp_path / "prueba.db")
    yield conexion
    conexion.close()
