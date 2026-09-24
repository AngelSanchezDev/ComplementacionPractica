from itertools import pairwise

import pytest

from validator_app.models import clientes, database, riesgo
from validator_app.models.errors import ValidationError


def test_rangos_riesgo_cubren_0_a_1000_sin_huecos(conn):
    rangos = riesgo.rangos_riesgo(conn)
    assert len(rangos) == 5
    assert rangos[0]["score_min"] == 0
    assert rangos[-1]["score_max"] == 1000
    for anterior, actual in pairwise(rangos):
        assert actual["score_min"] == anterior["score_max"] + 1


@pytest.mark.parametrize(
    ("score", "riesgo_esperado"),
    [
        (0, "Muy Alto"), (299, "Muy Alto"),
        (300, "Alto"), (549, "Alto"),
        (550, "Medio"), (749, "Medio"),
        (750, "Bajo"), (899, "Bajo"),
        (900, "Muy Bajo"), (1000, "Muy Bajo"),
    ],
)
def test_clasificar_score_limites(conn, score, riesgo_esperado):
    assert riesgo.clasificar_score(conn, score)["riesgo"] == riesgo_esperado


@pytest.mark.parametrize("score", [-1, 1001])
def test_clasificar_score_fuera_de_rango(conn, score):
    with pytest.raises(ValidationError):
        riesgo.clasificar_score(conn, score)


def test_resumen_por_riesgo_suma_total_clientes(conn):
    resumen = riesgo.resumen_por_riesgo(conn)
    assert len(resumen) == 5
    assert sum(fila["total"] for fila in resumen) == clientes.contar_clientes(conn)


def test_resumen_por_riesgo_incluye_niveles_en_cero(tmp_path, monkeypatch):
    monkeypatch.setattr(clientes, "CANTIDAD_DEMO", 0)
    monkeypatch.setattr(clientes, "CLIENTES_DEMO", [("12345678", "Unico Cliente Prueba", 100)])
    conexion = database.conectar(tmp_path / "vacia.db")
    resumen = riesgo.resumen_por_riesgo(conexion)
    assert len(resumen) == 5
    riesgos_con_datos = {f["riesgo"] for f in resumen if f["total"] > 0}
    assert riesgos_con_datos == {"Muy Alto"}
    conexion.close()
