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


def test_validar_score_texto():
    assert fields.validar_score_texto(" 750 ") == 750
    assert fields.validar_score_texto("0") == 0
    assert fields.validar_score_texto("1000") == 1000


def test_validar_score_texto_invalido():
    for valor in ("-1", "1001", "abc", "", "12.5"):
        with pytest.raises(ValueError):
            fields.validar_score_texto(valor)


def test_validar_nombre():
    assert fields.validar_nombre("  Juan   Perez  ") == "Juan Perez"


def test_validar_nombre_invalido():
    for valor in ("AB", "Juan123", "Juan_Perez"):
        with pytest.raises(ValueError):
            fields.validar_nombre(valor)


def test_permitir_digitos_acepta_solo_numeros_hasta_el_limite():
    filtro = fields.permitir_digitos(3)
    assert filtro("") is True
    assert filtro("1") is True
    assert filtro("123") is True
    assert filtro("1234") is False
    assert filtro("12a") is False
