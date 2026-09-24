from validator_app.views import entrada


def test_permitir_digitos_acepta_solo_numeros_hasta_el_limite():
    filtro = entrada.permitir_digitos(3)
    assert filtro("") is True
    assert filtro("1") is True
    assert filtro("123") is True
    assert filtro("1234") is False
    assert filtro("12a") is False
