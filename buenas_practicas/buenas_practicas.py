"""Práctica de la sesión 3: código limpio y capas.

Las pruebas están en `buenas_practicas/test_buenas_practicas.py`. Desde la raíz del proyecto:

    uv run pytest buenas_practicas -v
    uv run pytest buenas_practicas -k relevantes     # solo un ejercicio

El ejercicio 3 está en otro archivo, `buenas_practicas/arranque.py`.
"""

from __future__ import annotations

from fastapi import HTTPException

PALABRAS_VACIAS = frozenset({"de", "la", "el", "en", "y", "los", "las", "por", "con", "para"})


# 1. Nombres que explican -------------------------------------------------------------
# Diapositiva "Nombres que explican". NO cambie lo que hace: solo los nombres y los tipos.
#   - La función se llama fragmentos_relevantes (borre proc).
#   - Parámetros: resultados (lista de (texto, similitud)), limite = 5 y similitud_minima = 0.3,
#     todos con anotación de tipo, y también el tipo de retorno.
#   - Sin variables de una letra.
def fragmentos_relevantes(
    resultados: list[tuple[str, float]], limite: int = 5, similitud_minima: float = 0.3
) -> list[tuple[str, float]]:

    relevantes = [(texto, sim) for texto, sim in resultados if sim > similitud_minima]

    return relevantes[:limite]  # retorna desde el inicio : hasta el limite


# 2. Funciones pequeñas que hacen una cosa ---------------------------------------------------
# Diapositiva "Funciones pequeñas que hacen una cosa". procesar hace tres cosas: sepárelas en
#   limpiar(texto: str) -> str                    minúsculas y un solo espacio entre palabras
#   palabras_utiles(texto: str) -> list[str]      sin PALABRAS_VACIAS y de 3 letras o más
#   contar(palabras: list[str]) -> dict[str, int] cuántas veces aparece cada una
# y deje procesar como una función de tres líneas que llama a las otras tres.
def limpiar(texto: str) -> str:
    """Minúsculas y un solo espacio entre palabras."""
    return " ".join(texto.lower().split())


def palabras_utiles(texto: str) -> list[str]:
    """Palabras de 3 letras o más que no están en PALABRAS_VACIAS."""
    return [p for p in texto.split() if p not in PALABRAS_VACIAS and len(p) >= 3]


def contar(palabras: list[str]) -> dict[str, int]:
    """Cuántas veces aparece cada palabra."""
    # return {p: palabras.count(p) for p in palabras}
    conteo: dict[str, int] = {}
    for palabra in palabras:
        conteo[palabra] = conteo.get(palabra, 0) + 1

    return conteo


def procesar(texto: str) -> dict[str, int]:
    """Limpia el texto, descarta las palabras que no aportan y cuenta las que quedan."""
    texto = limpiar(texto)
    utiles = palabras_utiles(texto)
    return contar(utiles)


# 4. Cada capa habla su idioma -------------------------------------------------------------
# Diapositivas "Tres capas, una dirección" y "Cómo se ve una violación".
class ErrorAsistente(Exception):
    """Raíz de los errores del asistente."""


class DocumentoNoEncontrado(ErrorAsistente): ...


# Defina aquí PreguntaInvalida, hija de ErrorAsistente.


def validar_pregunta(pregunta: str) -> str:
    """Capa de aplicación: la pregunta sin espacios a los lados.

    Vacía o de más de 500 caracteres → PreguntaInvalida. Arréglela: hoy lanza un error de HTTP,
    y este archivo no debe importar nada de fastapi (borre el import de arriba).
    """
    pregunta = pregunta.strip()
    if not pregunta or len(pregunta) > 500:
        raise HTTPException(400, "Pregunta inválida")
    return pregunta


def codigo_http(error: Exception) -> int:
    """Capa de presentación: traduce un error a código HTTP.

    PreguntaInvalida → 400, DocumentoNoEncontrado → 404, cualquier otro error → 500.
    """
    raise NotImplementedError
