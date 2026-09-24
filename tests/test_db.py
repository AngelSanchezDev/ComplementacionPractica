import pytest

from validator_app.core import db


@pytest.fixture
def conn(tmp_path):
    conexion = db.conectar(tmp_path / "prueba.db")
    yield conexion
    conexion.close()


def test_crea_esquema_y_datos_demo(conn):
    assert conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == len(db.USUARIOS_DEMO)
    assert conn.execute("SELECT COUNT(*) FROM clientes").fetchone()[0] == len(db.CLIENTES_DEMO)


def test_reconectar_no_duplica_datos_demo(tmp_path):
    ruta = tmp_path / "prueba.db"
    db.conectar(ruta).close()
    conexion = db.conectar(ruta)
    assert conexion.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 1
    conexion.close()


def test_ruta_desde_variable_de_entorno(tmp_path, monkeypatch):
    ruta = tmp_path / "otra" / "bd.db"
    monkeypatch.setenv("JSCONNECT_DB", str(ruta))
    db.conectar().close()
    assert ruta.exists()


def test_login_correcto(conn):
    usuario = db.autenticar(conn, "admin", "admin123")
    assert usuario is not None
    assert usuario["usuario"] == "admin"


def test_login_password_incorrecta(conn):
    assert db.autenticar(conn, "admin", "otra") is None


def test_login_usuario_inexistente(conn):
    assert db.autenticar(conn, "nadie", "admin123") is None


def test_password_no_se_guarda_en_texto_plano(conn):
    fila = conn.execute("SELECT password_hash FROM usuarios WHERE usuario='admin'").fetchone()
    assert "admin123" not in fila["password_hash"]


def test_crear_usuario_y_autenticar(conn):
    db.crear_usuario(conn, "alumno", "clave", "Alumno")
    assert db.autenticar(conn, "alumno", "clave")["nombre"] == "Alumno"


def test_crear_usuario_duplicado(conn):
    with pytest.raises(db.ValidationError):
        db.crear_usuario(conn, "admin", "x")


def test_cobertura_siempre_si():
    assert db.validar_cobertura(0.0, 0.0)["hay_cobertura"] is True
    assert db.validar_cobertura(-11.9, -77.0)["cobertura"] == "SI"


def test_score_dni_registrado(conn):
    score = db.validar_score(conn, "12345678")
    assert score["valor"] == 720
    assert score["riesgo"] == "BAJO"
    assert score["documento"] == "12345678"


def test_score_dni_desconocido(conn):
    assert db.validar_score(conn, "99999999") is None


def test_registrar_cliente_actualiza_score(conn):
    db.registrar_cliente(conn, "12345678", "Juan Perez", 800, "MUY BAJO")
    assert db.validar_score(conn, "12345678")["valor"] == 800


def test_registrar_cliente_dni_invalido(conn):
    with pytest.raises(db.ValidationError):
        db.registrar_cliente(conn, "1234", "X", 500)


def test_validar_devuelve_cobertura_y_score(conn):
    resultado = db.validar(conn, -11.95, -77.04, "87654321")
    assert resultado["cobertura"]["hay_cobertura"] is True
    assert resultado["score"]["valor"] == 580
