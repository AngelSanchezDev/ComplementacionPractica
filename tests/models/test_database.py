import sqlite3

from validator_app.models import clientes, database


def test_crea_esquema_y_datos_demo(conn):
    assert conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 1
    assert clientes.contar_clientes(conn) == 20


def test_reconectar_no_duplica_datos_demo(tmp_path, monkeypatch):
    monkeypatch.setattr(clientes, "CANTIDAD_DEMO", 20)
    ruta = tmp_path / "prueba.db"
    database.conectar(ruta).close()
    conexion = database.conectar(ruta)
    assert conexion.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 1
    assert clientes.contar_clientes(conexion) == 20
    conexion.close()


def test_ruta_desde_variable_de_entorno(tmp_path, monkeypatch):
    monkeypatch.setattr(clientes, "CANTIDAD_DEMO", 20)
    ruta = tmp_path / "otra" / "bd.db"
    monkeypatch.setenv("JSCONNECT_DB", str(ruta))
    database.conectar().close()
    assert ruta.exists()


def test_datos_demo_alcanzan_1000_clientes(tmp_path):
    conexion = database.conectar(tmp_path / "mil.db")
    assert clientes.contar_clientes(conexion) >= clientes.CANTIDAD_DEMO
    conexion.close()


def test_migracion_desde_esquema_v1(tmp_path):
    ruta = tmp_path / "vieja.db"
    viejo = sqlite3.connect(ruta)
    viejo.executescript(
        """
        CREATE TABLE clientes (
            dni TEXT PRIMARY KEY, nombre TEXT, score INTEGER, riesgo TEXT
        );
        INSERT INTO clientes VALUES ('11223344', 'Cliente Viejo Test', 720, 'BAJO');
        """
    )
    viejo.commit()
    viejo.close()

    conexion = database.conectar(ruta)
    cliente = clientes.obtener_cliente(conexion, "11223344")
    assert cliente is not None
    assert cliente["nombre"] == "Cliente Viejo Test"
    assert cliente["score"] == 720
    assert cliente["riesgo"] == "Medio"
    conexion.close()
