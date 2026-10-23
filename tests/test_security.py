from pathlib import Path

import pytest

from mcp_server.server import PROJECT_ROOT, _safe_path


def test_rechaza_ruta_que_sale_del_proyecto():
    with pytest.raises(ValueError):
        _safe_path("../archivo_fuera.txt")


def test_rechaza_ruta_absoluta_externa():
    ruta_externa = PROJECT_ROOT.parent / "archivo_fuera.txt"

    with pytest.raises(ValueError):
        _safe_path(str(ruta_externa))


def test_rechaza_ruta_con_byte_nulo():
    with pytest.raises(ValueError):
        _safe_path("archivo\x00.txt")


def test_acepta_ruta_dentro_del_proyecto():
    resultado = _safe_path("tests/test_mcp_server.py")

    assert resultado == (
        PROJECT_ROOT / "tests" / "test_mcp_server.py"
    ).resolve()
    assert resultado.is_relative_to(PROJECT_ROOT)
def test_rechaza_acceso_a_directorio_venv():
    with pytest.raises(ValueError):
        _safe_path(".venv/archivo.txt")


def test_rechaza_archivo_env():
    with pytest.raises(ValueError):
        _safe_path(".env")


def test_trunca_salida_larga():
    from mcp_server.server import MAX_OUTPUT_CHARS, _truncate

    texto = "A" * (MAX_OUTPUT_CHARS + 100)
    resultado = _truncate(texto)

    assert len(resultado) < len(texto)
    assert resultado.startswith("A")
    assert "salida truncada" in resultado
