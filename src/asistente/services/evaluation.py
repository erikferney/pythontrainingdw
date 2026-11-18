"""Sesión 13: evaluar la generación con un modelo como juez.

La recuperación se evalúa con pruebas deterministas (tests/evals). La generación no admite un
assert: hay muchas respuestas correctas y el modelo no es determinista. Por eso se mide con
casos y métricas, y un segundo modelo juzga cada respuesta con un veredicto auditable.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from pydantic import BaseModel, Field

from asistente.domain.ports import LLMProvider

JUEZ = """\
Eres un evaluador estricto. Recibes fragmentos, una pregunta, una respuesta esperada y una
respuesta generada. Una afirmación sin respaldo en los fragmentos hace la respuesta NO fiel,
aunque sea cierta. Si la respuesta esperada es "NO SABE", la correcta es abstenerse."""


class Veredicto(BaseModel):
    fiel: bool = Field(description="¿Toda afirmación de la respuesta está en los fragmentos?")
    correcta: bool = Field(description="¿Coincide con la respuesta esperada?")
    afirmaciones_sin_respaldo: list[str] = Field(default_factory=list)


@dataclass(frozen=True)
class Caso:
    pregunta: str
    esperada: str  # "NO SABE" si la respuesta no está en los documentos


# taller: s13
async def juzgar(
    juez: LLMProvider, caso: Caso, respuesta: str, fragmentos: Sequence[str]
) -> Veredicto:
    """Pide el veredicto al juez; los fragmentos van delimitados como datos, no instrucciones."""
    raise NotImplementedError


@dataclass(frozen=True)
class Metricas:
    fidelidad: float
    correccion: float
    casos: int


def resumir(veredictos: Sequence[Veredicto]) -> Metricas:
    """Proporción de respuestas fieles y correctas: la fila de la tabla de versiones."""
    n = len(veredictos) or 1
    return Metricas(
        fidelidad=sum(v.fiel for v in veredictos) / n,
        correccion=sum(v.correcta for v in veredictos) / n,
        casos=len(veredictos),
    )
