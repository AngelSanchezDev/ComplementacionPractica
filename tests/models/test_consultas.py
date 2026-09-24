import pytest

from validator_app.models import consultas, usuarios
from validator_app.models.errors import ValidationError


def test_validar_guarda_en_historial(conn):
    resultado = consultas.validar(conn, -11.95, -77.04, "87654321", usuario_id=1)
    assert resultado["cobertura"]["hay_cobertura"] is True
    assert resultado["score"]["valor"] == 580
    filas = consultas.historial(conn, usuario_id=1)
    assert len(filas) == 1
    assert filas[0]["dni"] == "87654321"


def test_historial_filtra_por_usuario(conn):
    usuarios.crear_usuario(conn, "otro", "clave", "Otro")
    otro = usuarios.autenticar(conn, "otro", "clave")
    consultas.validar(conn, -11.95, -77.04, "87654321", usuario_id=1)
    consultas.validar(conn, -11.95, -77.04, "12345678", usuario_id=otro["id"])
    assert len(consultas.historial(conn, usuario_id=1)) == 1
    assert len(consultas.historial(conn, usuario_id=otro["id"])) == 1


@pytest.mark.parametrize("clave", list(consultas.CONSULTAS_CATALOGO))
def test_ejecutar_consulta_catalogo_no_falla(conn, clave):
    columnas, filas = consultas.ejecutar_consulta_catalogo(conn, clave)
    assert len(columnas) > 0
    assert isinstance(filas, list)


def test_consulta_nunca_consultados_baja_tras_una_consulta(conn):
    _, filas_antes = consultas.ejecutar_consulta_catalogo(conn, "nunca_consultados")
    consultas.validar(conn, -11.95, -77.04, "12345678", usuario_id=None)
    _, filas_despues = consultas.ejecutar_consulta_catalogo(conn, "nunca_consultados")
    assert len(filas_despues) == len(filas_antes) - 1


def test_ejecutar_consulta_catalogo_clave_invalida(conn):
    with pytest.raises(ValidationError):
        consultas.ejecutar_consulta_catalogo(conn, "no-existe")
