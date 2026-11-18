"""Sesión 4: un proveedor nuevo sin tocar ningún archivo existente (abierto/cerrado).

Se registra a sí mismo al importarse; la raíz de composición (api/main.py) lo importa.
Con LLM_PROVIDER=eco, el asistente responde con la última pregunta en mayúsculas.
"""

from __future__ import annotations

from collections.abc import Sequence

from asistente.adapters.llm.providers import register_llm
from asistente.domain.models import Message


class EcoLLM:
    name = "eco"

    # taller: s04
    async def complete(self, messages: Sequence[Message], *, temperature: float = 0.2) -> str:
        raise NotImplementedError


register_llm("eco", EcoLLM)
