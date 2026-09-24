import pytest

from validator_app.models import usuarios
from validator_app.models.errors import ValidationError


def test_login_correcto(conn):
    usuario = usuarios.autenticar(conn, "admin", "admin123")
    assert usuario is not None
    assert usuario["usuario"] == "admin"


def test_login_password_incorrecta(conn):
    assert usuarios.autenticar(conn, "admin", "otra") is None


def test_login_usuario_inexistente(conn):
    assert usuarios.autenticar(conn, "nadie", "admin123") is None


def test_password_no_se_guarda_en_texto_plano(conn):
    fila = conn.execute("SELECT password_hash FROM usuarios WHERE usuario='admin'").fetchone()
    assert "admin123" not in fila["password_hash"]


def test_crear_usuario_y_autenticar(conn):
    usuarios.crear_usuario(conn, "alumno", "clave", "Alumno")
    assert usuarios.autenticar(conn, "alumno", "clave")["nombre"] == "Alumno"


def test_crear_usuario_duplicado(conn):
    with pytest.raises(ValidationError):
        usuarios.crear_usuario(conn, "admin", "x")
