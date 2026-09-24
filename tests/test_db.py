from itertools import pairwise

import pytest

from validator_app.core import db


@pytest.fixture
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "CANTIDAD_DEMO", 20)
    conexion = db.conectar(tmp_path / "prueba.db")
    yield conexion
    conexion.close()


def test_crea_esquema_y_datos_demo(conn):
    assert conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == len(db.USUARIOS_DEMO)
    assert db.contar_clientes(conn) == 20


def test_rangos_riesgo_cubren_0_a_1000_sin_huecos(conn):
    rangos = db.rangos_riesgo(conn)
    assert len(rangos) == 5
    assert rangos[0]["score_min"] == 0
    assert rangos[-1]["score_max"] == 1000
    for anterior, actual in pairwise(rangos):
        assert actual["score_min"] == anterior["score_max"] + 1


@pytest.mark.parametrize(
    ("score", "riesgo"),
    [
        (0, "Muy Alto"), (299, "Muy Alto"),
        (300, "Alto"), (549, "Alto"),
        (550, "Medio"), (749, "Medio"),
        (750, "Bajo"), (899, "Bajo"),
        (900, "Muy Bajo"), (1000, "Muy Bajo"),
    ],
)
def test_clasificar_score_limites(conn, score, riesgo):
    assert db.clasificar_score(conn, score)["riesgo"] == riesgo


@pytest.mark.parametrize("score", [-1, 1001])
def test_clasificar_score_fuera_de_rango(conn, score):
    with pytest.raises(db.ValidationError):
        db.clasificar_score(conn, score)


def test_reconectar_no_duplica_datos_demo(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "CANTIDAD_DEMO", 20)
    ruta = tmp_path / "prueba.db"
    db.conectar(ruta).close()
    conexion = db.conectar(ruta)
    assert conexion.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 1
    assert db.contar_clientes(conexion) == 20
    conexion.close()


def test_ruta_desde_variable_de_entorno(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "CANTIDAD_DEMO", 20)
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
    assert score["riesgo"] == "Medio"
    assert score["documento"] == "12345678"


def test_score_dni_desconocido(conn):
    assert db.validar_score(conn, "99999999") is None


def test_crear_cliente(conn):
    db.crear_cliente(conn, "40000001", "Pedro Suarez Leon", 900)
    assert db.validar_score(conn, "40000001")["valor"] == 900


def test_crear_cliente_dni_duplicado(conn):
    with pytest.raises(db.ValidationError):
        db.crear_cliente(conn, "12345678", "Otro Nombre Mas", 500)


def test_crear_cliente_dni_invalido(conn):
    with pytest.raises(db.ValidationError):
        db.crear_cliente(conn, "1234", "Nombre Valido", 500)


def test_crear_cliente_nombre_invalido(conn):
    with pytest.raises(db.ValidationError):
        db.crear_cliente(conn, "40000002", "AB", 500)


def test_crear_cliente_score_invalido(conn):
    with pytest.raises(db.ValidationError):
        db.crear_cliente(conn, "40000003", "Nombre Valido Test", 1500)


def test_actualizar_cliente(conn):
    db.actualizar_cliente(conn, "12345678", "Juan Perez Actualizado", 800)
    cliente = db.obtener_cliente(conn, "12345678")
    assert cliente["nombre"] == "Juan Perez Actualizado"
    assert cliente["score"] == 800


def test_actualizar_cliente_inexistente(conn):
    with pytest.raises(db.ValidationError):
        db.actualizar_cliente(conn, "40000004", "Nombre Valido Test", 500)


def test_eliminar_cliente(conn):
    db.eliminar_cliente(conn, "12345678")
    assert db.obtener_cliente(conn, "12345678") is None


def test_eliminar_cliente_inexistente(conn):
    with pytest.raises(db.ValidationError):
        db.eliminar_cliente(conn, "40000005")


def test_existe_dni(conn):
    assert db.existe_dni(conn, "12345678") is True
    assert db.existe_dni(conn, "40000006") is False


def test_buscar_clientes_por_dni(conn):
    filas, total = db.buscar_clientes(conn, "1234")
    assert total >= 1
    assert all(f["dni"].startswith("1234") for f in filas)


def test_buscar_clientes_por_nombre(conn):
    filas, total = db.buscar_clientes(conn, "Juan")
    assert total >= 1
    assert all("juan" in f["nombre"].lower() for f in filas)


def test_buscar_clientes_paginacion(conn):
    filas, total = db.buscar_clientes(conn, "", limite=5, offset=0)
    assert total == db.contar_clientes(conn)
    assert len(filas) == 5


def test_generar_clientes_es_determinista(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "CANTIDAD_DEMO", 0)
    conn1 = db.conectar(tmp_path / "a.db")
    conn2 = db.conectar(tmp_path / "b.db")
    n1 = db.generar_clientes(conn1, 200, semilla=7)
    n2 = db.generar_clientes(conn2, 200, semilla=7)
    assert n1 == n2 == 200
    dnis1 = {f[0] for f in conn1.execute("SELECT dni FROM clientes ORDER BY dni")}
    dnis2 = {f[0] for f in conn2.execute("SELECT dni FROM clientes ORDER BY dni")}
    assert dnis1 == dnis2
    conn1.close()
    conn2.close()


def test_datos_demo_alcanzan_1000_clientes(tmp_path):
    conexion = db.conectar(tmp_path / "mil.db")
    assert db.contar_clientes(conexion) >= db.CANTIDAD_DEMO
    conexion.close()


def test_migracion_desde_esquema_v1(tmp_path):
    import sqlite3

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

    conexion = db.conectar(ruta)
    cliente = db.obtener_cliente(conexion, "11223344")
    assert cliente is not None
    assert cliente["nombre"] == "Cliente Viejo Test"
    assert cliente["score"] == 720
    assert cliente["riesgo"] == "Medio"
    conexion.close()


def test_validar_guarda_en_historial(conn):
    resultado = db.validar(conn, -11.95, -77.04, "87654321", usuario_id=1)
    assert resultado["cobertura"]["hay_cobertura"] is True
    assert resultado["score"]["valor"] == 580
    filas = db.historial(conn, usuario_id=1)
    assert len(filas) == 1
    assert filas[0]["dni"] == "87654321"


def test_historial_filtra_por_usuario(conn):
    db.crear_usuario(conn, "otro", "clave", "Otro")
    otro = db.autenticar(conn, "otro", "clave")
    db.validar(conn, -11.95, -77.04, "87654321", usuario_id=1)
    db.validar(conn, -11.95, -77.04, "12345678", usuario_id=otro["id"])
    assert len(db.historial(conn, usuario_id=1)) == 1
    assert len(db.historial(conn, usuario_id=otro["id"])) == 1
