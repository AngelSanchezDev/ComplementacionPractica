import pytest

from validator_app.gui import fields


def test_parse_coordenadas():
    assert fields.parse_coordenadas("-11.956037627741102, -77.04065381800075") == (
        -11.956037627741102,
        -77.04065381800075,
    )


def test_parse_coordenadas_con_espacios():
    assert fields.parse_coordenadas("-11.956 , -77.040") == (-11.956, -77.040)


def test_parse_coordenadas_invalidas():
    with pytest.raises(ValueError):
        fields.parse_coordenadas("solo-una-coordenada")
    with pytest.raises(ValueError):
        fields.parse_coordenadas("-91.0, -77.0")
    with pytest.raises(ValueError):
        fields.parse_coordenadas("-11.0, -181.0")


def test_validar_dni():
    assert fields.validar_dni(" 12345678 ") == "12345678"


def test_validar_dni_invalido():
    for valor in ("1234567", "123456789", "1234567A", ""):
        with pytest.raises(ValueError):
            fields.validar_dni(valor)
