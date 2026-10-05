"""Sesión 1 — Prueba diagnóstica (45 min). Implemente cada función y ejecute:

    uv run pytest diagnostico -q

Mide: tipado, colecciones, comprensiones, funciones de orden superior, generadores,
manejo de errores, dataclasses y context managers. No requiere librerías externas.
"""

from __future__ import annotations

import functools
import string
from collections import Counter
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass


# 1. Comprensiones -----------------------------------------------------------
def palabras_por_longitud(texto: str) -> dict[int, list[str]]:
    """Agrupa palabras únicas (minúsculas, sin puntuación) por longitud, ordenadas."""
    # limpiar signos de puntuación y convertir a miniscula
    lst_txt_clean = texto.translate(str.maketrans("", "", string.punctuation)).lower()

    # se genera un listado de palabras únicas
    lst_words = set(lst_txt_clean.split())

    resultado = {}

    for word in lst_words:
        longitud = len(word)
        resultado.setdefault(longitud, []).append(word)

    return {clave: sorted(resultado[clave]) for clave in sorted(resultado)}


# 2. Colecciones -------------------------------------------------------------
def top_n(frecuencias: Iterable[str], n: int) -> list[tuple[str, int]]:
    """Los n elementos más frecuentes; empate → orden alfabético."""

    # 1. Contar la frecuencia de cada palabra en el iterable
    conteo = Counter(frecuencias)

    # 2. Ordenar las palabras por frecuencia y alfabéticamente
    resultado = sorted(conteo.items(), key=lambda x: (-x[1], x[0]))

    return resultado[:n]


# 3. Funciones de orden superior / closures ----------------------------------
def reintentar(veces: int) -> Callable[[Callable[..., object]], Callable[..., object]]:
    """Decorador: reintenta la función hasta `veces` si lanza excepción; luego la propaga."""

    def decorador(funcion: Callable[..., object]) -> Callable[..., object]:
        @functools.wraps(funcion)
        def wrapper(*args: object, **kwargs: object) -> object:
            intentos_totales = veces

            for intento in range(1, intentos_totales + 1):
                try:
                    # Intenta ejecutar la función original
                    return funcion(*args, **kwargs)
                except Exception as e:
                    # Si falla en el último intento, lanza la excepción original
                    if intento == intentos_totales:
                        raise e
                    print(f"⚠️ Intento {intento}/{intentos_totales} falló: {e}. Reintentando...")

        return wrapper

    return decorador


# 4. Generadores -------------------------------------------------------------
def en_lotes[T](items: Iterable[T], tamano: int) -> Iterator[list[T]]:
    """Entrega listas de `tamano` elementos (la última puede ser menor). Perezoso."""
    lote: list[T] = []
    for item in items:
        lote.append(item)
        if len(lote) == tamano:
            yield lote
            lote = []
    if lote:
        yield lote


# 5. Dataclasses + propiedades -----------------------------------------------
@dataclass
class Factura:
    subtotal: float
    iva: float = 0.19

    @property
    def total(self) -> float:
        raise NotImplementedError

    def __post_init__(self) -> None:
        """Debe lanzar ValueError si subtotal < 0 o iva fuera de [0, 1]."""
        raise NotImplementedError


# 6. Context managers --------------------------------------------------------
class Cronometro:
    """with Cronometro() as c: ...  → c.segundos tiene la duración del bloque."""

    def __enter__(self) -> Cronometro:
        raise NotImplementedError

    def __exit__(self, *exc: object) -> None:
        raise NotImplementedError
