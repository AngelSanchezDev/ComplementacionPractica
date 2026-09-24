import pytest

from validator_app.models import clientes
from validator_app.models.errors import ValidationError


def test_cobertura_siempre_si():
    assert clientes.validar_cobertura(0.0, 0.0)["hay_cobertura"] is True
    assert clientes.validar_cobertura(-11.9, -77.0)["cobertura"] == "SI"


def test_score_dni_registrado(conn):
    score = clientes.validar_score(conn, "12345678")
    assert score["valor"] == 720
    assert score["riesgo"] == "Medio"
    assert score["documento"] == "12345678"


def test_score_dni_desconocido(conn):
    assert clientes.validar_score(conn, "99999999") is None


def test_crear_cliente(conn):
    clientes.crear_cliente(conn, "40000001", "Pedro Suarez Leon", 900)
    assert clientes.validar_score(conn, "40000001")["valor"] == 900


def test_crear_cliente_dni_duplicado(conn):
    with pytest.raises(ValidationError):
        clientes.crear_cliente(conn, "12345678", "Otro Nombre Mas", 500)


def test_crear_cliente_dni_invalido(conn):
    with pytest.raises(ValidationError):
        clientes.crear_cliente(conn, "1234", "Nombre Valido", 500)


def test_crear_cliente_nombre_invalido(conn):
    with pytest.raises(ValidationError):
        clientes.crear_cliente(conn, "40000002", "AB", 500)


def test_crear_cliente_score_invalido(conn):
    with pytest.raises(ValidationError):
        clientes.crear_cliente(conn, "40000003", "Nombre Valido Test", 1500)


def test_actualizar_cliente(conn):
    clientes.actualizar_cliente(conn, "12345678", "Juan Perez Actualizado", 800)
    cliente = clientes.obtener_cliente(conn, "12345678")
    assert cliente["nombre"] == "Juan Perez Actualizado"
    assert cliente["score"] == 800


def test_actualizar_cliente_inexistente(conn):
    with pytest.raises(ValidationError):
        clientes.actualizar_cliente(conn, "40000004", "Nombre Valido Test", 500)


def test_eliminar_cliente(conn):
    clientes.eliminar_cliente(conn, "12345678")
    assert clientes.obtener_cliente(conn, "12345678") is None


def test_eliminar_cliente_inexistente(conn):
    with pytest.raises(ValidationError):
        clientes.eliminar_cliente(conn, "40000005")


def test_existe_dni(conn):
    assert clientes.existe_dni(conn, "12345678") is True
    assert clientes.existe_dni(conn, "40000006") is False


def test_buscar_clientes_por_dni(conn):
    filas, total = clientes.buscar_clientes(conn, "1234")
    assert total >= 1
    assert all(f["dni"].startswith("1234") for f in filas)


def test_buscar_clientes_por_nombre(conn):
    filas, total = clientes.buscar_clientes(conn, "Juan")
    assert total >= 1
    assert all("juan" in f["nombre"].lower() for f in filas)


def test_buscar_clientes_por_riesgo(conn):
    filas, total = clientes.buscar_clientes(conn, riesgo="Muy Alto")
    assert total >= 1
    assert all(f["riesgo"] == "Muy Alto" for f in filas)


def test_buscar_clientes_por_texto_y_riesgo_combinados(conn):
    clientes.crear_cliente(conn, "40000010", "Juan Perez Combinado", 800)
    filas, total = clientes.buscar_clientes(conn, texto="Juan", riesgo="Bajo")
    assert total >= 1
    assert all("juan" in f["nombre"].lower() and f["riesgo"] == "Bajo" for f in filas)


def test_buscar_clientes_paginacion(conn):
    filas, total = clientes.buscar_clientes(conn, "", limite=5, offset=0)
    assert total == clientes.contar_clientes(conn)
    assert len(filas) == 5


def test_generar_clientes_es_determinista(tmp_path, monkeypatch):
    from validator_app.models import database

    monkeypatch.setattr(clientes, "CANTIDAD_DEMO", 0)
    conn1 = database.conectar(tmp_path / "a.db")
    conn2 = database.conectar(tmp_path / "b.db")
    n1 = clientes.generar_clientes(conn1, 200, semilla=7)
    n2 = clientes.generar_clientes(conn2, 200, semilla=7)
    assert n1 == n2 == 200
    dnis1 = {f[0] for f in conn1.execute("SELECT dni FROM clientes ORDER BY dni")}
    dnis2 = {f[0] for f in conn2.execute("SELECT dni FROM clientes ORDER BY dni")}
    assert dnis1 == dnis2
    conn1.close()
    conn2.close()
