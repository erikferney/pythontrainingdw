"""Sesión 9: manejo de contexto. Resumir lo antiguo y conservar textual lo reciente."""

from __future__ import annotations

from asistente.domain.models import Conversation
from asistente.domain.ports import LLMProvider

RESUMIR = (
    "Resume en máximo 5 viñetas los datos de esta conversación que sigan siendo útiles: "
    "quién es el usuario, qué decidió, qué falta. No incluyas saludos ni repeticiones."
)


# taller: s09
async def compactar(
    conv: Conversation, llm: LLMProvider, *, conservar: int = 6, umbral: int = 20
) -> bool:
    """Si la conversación pasa de `umbral` mensajes, resume los antiguos con el modelo.

    Conserva textuales los últimos `conservar`. El resumen anterior entra en el nuevo, para no
    perder lo que ya se había resumido. Devuelve True si compactó.
    """
    raise NotImplementedError
