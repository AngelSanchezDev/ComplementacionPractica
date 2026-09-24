import pytest

from validator_app.controllers.validar_controller import ValidarController
from validator_app.models.errors import APIError


def test_validar_dni_registrado(conn):
    controller = ValidarController(conn, usuario=None)
    resultado = controller.validar("-11.95, -77.04", "12345678")
    assert resultado["cobertura"]["hay_cobertura"] is True
    assert resultado["score"]["valor"] == 720


def test_validar_coordenadas_invalidas_lanza_apierror(conn):
    """El ValueError de validaciones.py llega como errors.APIError, no ValueError."""
    controller = ValidarController(conn, usuario=None)
    with pytest.raises(APIError):
        controller.validar("no-son-coordenadas", "12345678")


def test_validar_dni_invalido_lanza_apierror(conn):
    controller = ValidarController(conn, usuario=None)
    with pytest.raises(APIError):
        controller.validar("-11.95, -77.04", "123")


def test_validar_guarda_usuario_id_de_la_sesion(conn):
    controller = ValidarController(conn, usuario={"id": 1, "usuario": "admin"})
    controller.validar("-11.95, -77.04", "87654321")
    from validator_app.models import consultas

    assert len(consultas.historial(conn, usuario_id=1)) == 1
