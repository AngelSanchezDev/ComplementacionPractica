import pytest

from validator_app.controllers.login_controller import LoginController
from validator_app.models.errors import APIError, LoginError


def test_iniciar_sesion_correcto(conn):
    controller = LoginController(conn)
    usuario = controller.iniciar_sesion("admin", "admin123")
    assert usuario["usuario"] == "admin"


def test_iniciar_sesion_incorrecto_lanza_apierror(conn):
    controller = LoginController(conn)
    with pytest.raises(APIError):
        controller.iniciar_sesion("admin", "mala")


def test_iniciar_sesion_incorrecto_es_login_error(conn):
    controller = LoginController(conn)
    with pytest.raises(LoginError):
        controller.iniciar_sesion("nadie", "loquesea")
