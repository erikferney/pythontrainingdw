"""Sesión 12: workflow de enrutamiento. El código decide el camino; el modelo, solo la ruta."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from asistente.agents.tools import Usuario
from asistente.domain.ports import LLMProvider
from asistente.services.rag import RagService

FUERA_DE_ALCANCE = "Solo puedo ayudar con temas de talento humano y políticas de la empresa."
ENRUTAR = (
    "Clasifica la pregunta de un empleado. 'politicas' si pregunta por reglas o procedimientos "
    "de la empresa; 'nomina' si pregunta por su saldo, pagos o vacaciones pendientes; "
    "'fuera_de_alcance' si no tiene que ver con talento humano."
)


class Ruta(BaseModel):
    destino: Literal["politicas", "nomina", "fuera_de_alcance"]


# taller: s12
async def atender(pregunta: str, usuario: Usuario, router: LLMProvider, rag: RagService) -> str:
    """Un modelo (puede ser uno pequeño) elige la ruta; cada ruta tiene su propio camino."""
    raise NotImplementedError
