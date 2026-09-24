import pytest

from validator_app.controllers.clientes_controller import ClientesController
from validator_app.models.errors import APIError


def test_crear_cliente_correcto(conn):
    controller = ClientesController(conn)
    controller.crear("40000099", "Cliente De Prueba", "700")
    assert controller.existe("40000099") is True


def test_crear_cliente_nombre_invalido_lanza_apierror(conn):
    """El ValueError de validaciones.py llega como errors.APIError."""
    controller = ClientesController(conn)
    with pytest.raises(APIError):
        controller.crear("40000098", "AB", "700")


def test_crear_cliente_dni_duplicado_lanza_apierror(conn):
    """El ValidationError del Modelo tambien llega como errors.APIError."""
    controller = ClientesController(conn)
    with pytest.raises(APIError):
        controller.crear("12345678", "Nombre Cualquiera", "500")


def test_existe_no_lanza_con_dni_incompleto(conn):
    controller = ClientesController(conn)
    assert controller.existe("1234") is False


def test_clasificar_preview_none_si_no_es_numero(conn):
    controller = ClientesController(conn)
    assert controller.clasificar_preview("") is None
    assert controller.clasificar_preview("abc") is None


def test_clasificar_preview_devuelve_riesgo(conn):
    controller = ClientesController(conn)
    info = controller.clasificar_preview("750")
    assert info["riesgo"] == "Bajo"


def test_actualizar_dni_inexistente_lanza_apierror(conn):
    controller = ClientesController(conn)
    with pytest.raises(APIError):
        controller.actualizar("40000097", "Nombre Cualquiera", "500")


def test_buscar_devuelve_lo_mismo_que_el_modelo(conn):
    controller = ClientesController(conn)
    filas, total = controller.buscar("Juan")
    assert total >= 1
    assert all("juan" in f["nombre"].lower() for f in filas)
