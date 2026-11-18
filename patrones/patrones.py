"""Práctica de la sesión 4: arquitectura, dominio y patrones, un ejercicio por tema.

Cada ejercicio dice qué hacer y en qué diapositiva se vio. Las pruebas están en
`patrones/test_patrones.py` y son la especificación. Ejecute, desde la raíz del proyecto:

    uv run pytest patrones -v           # todas
    uv run pytest patrones -k imports   # solo las de un ejercicio

Los ejercicios siguen el orden de la clase. Los demás de hoy están en el proyecto
(`src/asistente/...`) y en `fundamentos/s04_decoradores.py`.
"""

from __future__ import annotations

import ast  # noqa: F401  (lo necesita el ejercicio 1)
import sys  # noqa: F401  (lo necesita el ejercicio 1)
from dataclasses import dataclass, field  # noqa: F401
from datetime import date
from pathlib import Path
from typing import Protocol


# 1. La regla de dependencia, verificada por una prueba ------------------------------------
# Diapositiva "La regla de dependencia".
def imports_externos(codigo: str) -> set[str]:
    """Los paquetes de afuera que importa un código fuente: ni de la biblioteca estándar
    ni del propio proyecto (`asistente`).

    De cada import se toma solo el primer nombre: `from fastapi.responses import X` → "fastapi".
    Cuentan también los imports dentro de funciones.

    imports_externos("import os\\nfrom fastapi import FastAPI")   → {"fastapi"}
    imports_externos("from asistente.domain import models")      → set()
    """
    raise NotImplementedError


def revisar_carpeta(carpeta: Path) -> dict[str, set[str]]:
    """Revisa cada archivo .py de la carpeta (sin subcarpetas) con `imports_externos`.

    Devuelve {nombre del archivo: paquetes externos} SOLO de los archivos que importan algo
    de afuera. Una carpeta limpia devuelve {}.
    """
    raise NotImplementedError


# 2. Lenguaje ubicuo --------------------------------------------------------------------------
# Diapositiva "Lenguaje ubicuo". El área de talento humano dice: "una política está vigente
# desde una fecha y, a veces, hasta otra; el último día también cuenta".
class Politica:
    """Dataclass inmutable con cuatro campos, en este orden:
        codigo: str               p. ej. "TH-07"
        titulo: str
        vigente_desde: date
        vigente_hasta: date | None = None     None: sin fecha de fin

    - vigente_hasta anterior a vigente_desde → ValueError (en __post_init__)
    - método esta_vigente(en: date) -> bool, con los dos extremos incluidos
    """


# 3. Agregados: las reglas de conjunto viven en la raíz ----------------------------------------
# Diapositiva "Agregados: qué se guarda junto".
@dataclass
class Coleccion:
    """Raíz del agregado: un grupo de políticas, p. ej. "Talento humano".

    Regla del conjunto: dos políticas de la misma colección no pueden tener el mismo código.
    """

    nombre: str
    _politicas: dict[str, Politica] = field(default_factory=dict)

    def agregar(self, politica: Politica) -> None:
        """Agrega la política. Si ya hay una con ese código → ValueError con el código."""
        raise NotImplementedError

    def retirar(self, codigo: str) -> Politica:
        """Quita la política y la devuelve. Si no está → LookupError con el código."""
        raise NotImplementedError

    def vigentes(self, en: date) -> list[Politica]:
        """Las políticas vigentes en esa fecha, ordenadas por código."""
        raise NotImplementedError

    # Agregue la propiedad `politicas`: una TUPLA con las políticas, en el orden en que se
    # agregaron, para que desde afuera nadie se salte la regla del código repetido.


# 4. Repository: una colección que oculta el almacenamiento ------------------------------------
# Diapositiva "Repository: una colección que oculta el almacenamiento".
class RepositorioColecciones(Protocol):
    def guardar(self, coleccion: Coleccion) -> None: ...
    def obtener(self, nombre: str) -> Coleccion | None: ...
    def nombres(self) -> list[str]: ...


class ColeccionesEnMemoria:
    """Cumple RepositorioColecciones guardando en un diccionario {nombre: Coleccion}.

    - guardar: agrega, o reemplaza la que tenga el mismo nombre
    - obtener: la colección, o None si no existe
    - nombres: los nombres, ordenados alfabéticamente
    """


def politicas_vigentes(repo: RepositorioColecciones, nombre: str, en: date) -> list[Politica]:
    """Caso de uso: las políticas vigentes de una colección. Usa SOLO los métodos del
    protocolo (las pruebas le pasan otro repositorio). Colección inexistente → LookupError.
    """
    raise NotImplementedError


# 5. Strategy: el algoritmo es intercambiable -------------------------------------------------
# Diapositiva "Strategy: el algoritmo es intercambiable".
class Fragmentador(Protocol):
    def partir(self, texto: str) -> list[str]: ...


class PorLongitud:
    """Estrategia 1, dataclass inmutable con un campo `maximo: int`.

    - maximo menor que 1 → ValueError
    - partir(texto): pedazos de `maximo` caracteres seguidos ("abcde", maximo 2 →
      ["ab", "cd", "e"]); texto vacío → []
    """


class PorParrafos:
    """Estrategia 2, sin campos. partir(texto): los párrafos (separados por una línea en
    blanco, "\\n\\n"), sin espacios a los lados y sin los que quedan vacíos.
    """


def fragmentar(documentos: list[str], estrategia: Fragmentador) -> list[tuple[int, str]]:
    """Parte cada documento con la estrategia que le pasen. Devuelve (posición del documento
    en la lista, fragmento), en orden. No pregunta qué estrategia es: solo llama a `partir`.
    """
    raise NotImplementedError
