"""Pruebas de la práctica de la sesión 3. Desde la raíz del proyecto:

uv run pytest buenas_practicas -v
"""

import importlib
import inspect
import os
import runpy
import sys

import pytest

PREFIJO = os.getenv("PRACTICA", "")
_m = importlib.import_module(PREFIJO + "buenas_practicas")

RESULTADOS = [("a", 0.9), ("b", 0.2), ("c", 0.5), ("d", 0.31), ("e", 0.3)]


# 1. Nombres que explican -------------------------------------------------------------
def test_fragmentos_relevantes_hace_lo_mismo():
    f = _m.fragmentos_relevantes
    assert f(RESULTADOS) == [("a", 0.9), ("c", 0.5), ("d", 0.31)]
    assert f(RESULTADOS, limite=2) == [("a", 0.9), ("c", 0.5)]
    assert f(resultados=RESULTADOS, similitud_minima=0.6) == [("a", 0.9)]


def test_fragmentos_relevantes_nombres_y_tipos():
    assert not hasattr(_m, "proc"), "borre proc: el nombre nuevo la reemplaza"
    firma = inspect.signature(_m.fragmentos_relevantes)
    assert list(firma.parameters) == ["resultados", "limite", "similitud_minima"]
    anotaciones = _m.fragmentos_relevantes.__annotations__
    assert set(anotaciones) == {"resultados", "limite", "similitud_minima", "return"}


# 2. Funciones pequeñas ---------------------------------------------------------------------
def test_pequenas_limpiar():
    assert _m.limpiar("  Días   DE vacaciones ") == "días de vacaciones"


def test_pequenas_palabras_utiles():
    assert _m.palabras_utiles("días de vacaciones en la sede y ya") == [
        "días",
        "vacaciones",
        "sede",
    ]


def test_pequenas_contar():
    assert _m.contar(["sol", "mar", "sol"]) == {"sol": 2, "mar": 1}
    assert _m.contar([]) == {}


def test_pequenas_procesar_solo_coordina():
    assert _m.procesar("  Días de   VACACIONES y días ") == {"días": 2, "vacaciones": 1}
    cuerpo = [
        linea
        for linea in inspect.getsource(_m.procesar).splitlines()[1:]
        if linea.strip() and not linea.strip().startswith(('"""', "#"))
    ]
    assert len(cuerpo) <= 3, "procesar debería solo llamar a limpiar, palabras_utiles y contar"


# 3. Importar no debería hacer nada ----------------------------------------------------------
def _importar_de_nuevo():
    nombre = PREFIJO + "arranque"
    sys.modules.pop(nombre, None)
    return importlib.import_module(nombre)


def test_arranque_importar_no_conecta():
    modulo = _importar_de_nuevo()
    assert modulo.LLAMADAS == [], "importar el módulo llamó a conectar()"
    assert modulo.main() == "usando cliente-ollama"
    assert modulo.LLAMADAS == ["conectar"]


def test_arranque_se_puede_ejecutar(capsys):
    modulo = _importar_de_nuevo()
    runpy.run_path(modulo.__file__, run_name="__main__")
    assert capsys.readouterr().out == "usando cliente-ollama\n"


# 4. Cada capa habla su idioma -------------------------------------------------------------
def test_capas_la_aplicacion_no_conoce_http():
    assert "fastapi" not in inspect.getsource(_m), "la capa de aplicación no importa fastapi"
    assert issubclass(_m.PreguntaInvalida, _m.ErrorAsistente)
    assert _m.validar_pregunta("  ¿cuántos días?  ") == "¿cuántos días?"
    for mala in ["   ", "x" * 501]:
        with pytest.raises(_m.PreguntaInvalida):
            _m.validar_pregunta(mala)


def test_capas_la_presentacion_traduce():
    assert _m.codigo_http(_m.PreguntaInvalida("vacía")) == 400
    assert _m.codigo_http(_m.DocumentoNoEncontrado("d1")) == 404
    assert _m.codigo_http(_m.ErrorAsistente("otro")) == 500
    assert _m.codigo_http(KeyError("x")) == 500
