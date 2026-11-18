"""Sesiones 2 y 8: envoltorios de proveedores (patrón decorador, composición).

RetryingLLM reintenta con espera creciente y algo de azar SOLO ante errores transitorios
(ProviderUnavailableError). Una llave inválida o una petición mal formada fallan de inmediato.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable, Sequence

from asistente.domain.models import Message
from asistente.domain.ports import LLMProvider

log = logging.getLogger(__name__)


class RetryingLLM:
    def __init__(
        self,
        inner: LLMProvider,
        *,
        attempts: int = 4,
        base_delay: float = 1.0,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        if attempts < 1:
            raise ValueError("attempts debe ser al menos 1")
        self.inner = inner
        self.name = f"{inner.name}+reintentos"
        self._attempts = attempts
        self._base = base_delay
        self._sleep = sleep

    # taller: s08
    async def complete(self, messages: Sequence[Message], *, temperature: float = 0.2) -> str:
        """Espera base·2^n más un azar de hasta `base`, para que mil clientes no choquen juntos."""
        raise NotImplementedError
