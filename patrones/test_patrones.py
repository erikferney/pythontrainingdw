"""Pruebas de la práctica de la sesión 4. Son la especificación: no las modifique."""

import dataclasses
import importlib
import os
from datetime import date
from pathlib import Path

import pytest

_m = importlib.import_module(os.getenv("PRACTICA", "") + "patrones")

DOMINIO = Path(__file__).resolve().parents[1] / "src" / "asistente" / "domain"
ENE_1, JUN_30, DIC_31 = date(2026, 1, 1), date(2026, 6, 30), date(2026, 12, 31)


# 1 ------------------------------------------------------------------------------------------
def test_imports_externos():
    codigo = (
        "from __future__ import annotations\n"
        "import os, json\n"
        "from fastapi.responses import JSONResponse\n"
        "from asistente.domain.models import Document\n"
        "def f():\n"
        "    import openai\n"
    )
    assert _m.imports_externos(codigo) == {"fastapi", "openai"}
    assert _m.imports_externos("from collections.abc import Sequence") == set()


def test_imports_revisar_carpeta(tmp_path):
    (tmp_path / "limpio.py").write_text("import uuid\n", encoding="utf-8")
    (tmp_path / "sucio.py").write_text("import pydantic\nimport re\n", encoding="utf-8")
    (tmp_path / "notas.txt").write_text("import fastapi\n", encoding="utf-8")
    assert _m.revisar_carpeta(tmp_path) == {"sucio.py": {"pydantic"}}


def test_imports_el_dominio_del_proyecto_esta_limpio():
    assert DOMINIO.is_dir(), "corra las pruebas desde la raíz del proyecto"
    assert _m.revisar_carpeta(DOMINIO) == {}


# 2 ------------------------------------------------------------------------------------------
def test_politica_es_inmutable_y_valida():
    p = _m.Politica("TH-07", "Vacaciones", ENE_1, JUN_30)
    assert [f.name for f in dataclasses.fields(p)] == [
        "codigo",
        "titulo",
        "vigente_desde",
        "vigente_hasta",
    ]
    with pytest.raises(dataclasses.FrozenInstanceError):
        p.titulo = "otra"
    with pytest.raises(ValueError):
        _m.Politica("TH-08", "Al revés", JUN_30, ENE_1)
    assert _m.Politica("TH-09", "Abierta", ENE_1).vigente_hasta is None


def test_politica_esta_vigente():
    p = _m.Politica("TH-07", "Vacaciones", ENE_1, JUN_30)
    assert p.esta_vigente(ENE_1) and p.esta_vigente(JUN_30)  # los extremos cuentan
    assert not p.esta_vigente(date(2025, 12, 31))
    assert not p.esta_vigente(date(2026, 7, 1))
    assert _m.Politica("TH-09", "Abierta", ENE_1).esta_vigente(date(2040, 1, 1))


# 3 ------------------------------------------------------------------------------------------
def _coleccion():
    c = _m.Coleccion("Talento humano")
    c.agregar(_m.Politica("TH-07", "Vacaciones", ENE_1, JUN_30))
    c.agregar(_m.Politica("TH-02", "Viáticos", ENE_1))
    return c


def test_coleccion_agregar_y_regla_del_codigo():
    c = _coleccion()
    assert [p.codigo for p in c.politicas] == ["TH-07", "TH-02"]
    assert isinstance(c.politicas, tuple)
    with pytest.raises(ValueError, match="TH-07"):
        c.agregar(_m.Politica("TH-07", "Otra con el mismo código", ENE_1))


def test_coleccion_retirar_y_vigentes():
    c = _coleccion()
    assert [p.codigo for p in c.vigentes(JUN_30)] == ["TH-02", "TH-07"]
    assert [p.codigo for p in c.vigentes(DIC_31)] == ["TH-02"]
    assert c.retirar("TH-02").titulo == "Viáticos"
    assert [p.codigo for p in c.politicas] == ["TH-07"]
    with pytest.raises(LookupError, match="TH-99"):
        c.retirar("TH-99")


# 4 ------------------------------------------------------------------------------------------
def test_repositorio_en_memoria():
    repo = _m.ColeccionesEnMemoria()
    assert repo.obtener("Talento humano") is None and repo.nombres() == []
    repo.guardar(_coleccion())
    repo.guardar(_m.Coleccion("Compras"))
    nueva = _m.Coleccion("Talento humano")
    repo.guardar(nueva)  # mismo nombre: reemplaza
    assert repo.nombres() == ["Compras", "Talento humano"]
    assert repo.obtener("Talento humano") is nueva


class RepositorioDePrueba:
    """Otro repositorio: solo tiene los tres métodos del protocolo."""

    def __init__(self, *colecciones):
        self._datos = {c.nombre: c for c in colecciones}

    def guardar(self, coleccion):
        self._datos[coleccion.nombre] = coleccion

    def obtener(self, nombre):
        return self._datos.get(nombre)

    def nombres(self):
        return sorted(self._datos)


def test_repositorio_el_caso_de_uso_solo_usa_el_protocolo():
    repo = RepositorioDePrueba(_coleccion())
    vigentes = _m.politicas_vigentes(repo, "Talento humano", DIC_31)
    assert [p.codigo for p in vigentes] == ["TH-02"]
    with pytest.raises(LookupError):
        _m.politicas_vigentes(repo, "Compras", DIC_31)


# 5 ------------------------------------------------------------------------------------------
def test_estrategia_por_longitud():
    assert _m.PorLongitud(2).partir("abcde") == ["ab", "cd", "e"]
    assert _m.PorLongitud(10).partir("") == []
    with pytest.raises(ValueError):
        _m.PorLongitud(0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        _m.PorLongitud(3).maximo = 4


def test_estrategia_por_parrafos():
    texto = "  Primero.  \n\nSegundo\ncon dos líneas.\n\n\n\n"
    assert _m.PorParrafos().partir(texto) == ["Primero.", "Segundo\ncon dos líneas."]


def test_estrategia_fragmentar_no_pregunta_cual_es():
    class Palabras:  # una tercera estrategia, que el ejercicio no conoce
        def partir(self, texto):
            return texto.split()

    assert _m.fragmentar(["a b", "", "c"], Palabras()) == [(0, "a"), (0, "b"), (2, "c")]
    assert _m.fragmentar(["abc", "de"], _m.PorLongitud(2)) == [(0, "ab"), (0, "c"), (1, "de")]
    for clase in (_m.PorLongitud, _m.PorParrafos):
        assert clase.__bases__ == (object,), "las estrategias no heredan de nada"
