"""Sesiones 6, 9 y 13: reglas del servicio RAG."""

import asyncio

import pytest
from conftest import POLITICA, respuesta_json

from asistente.adapters.embeddings.providers import HashingEmbedding
from asistente.adapters.persistence.memory import InMemoryStore, InMemoryUnitOfWork
from asistente.domain.errors import ProviderUnavailableError
from asistente.domain.models import Document
from asistente.services.rag import RagService


def servicio(llm, store=None, **kwargs):
    store = store or InMemoryStore()
    return RagService(lambda: InMemoryUnitOfWork(store), HashingEmbedding(), llm, **kwargs)


# taller: s06
async def test_el_modelo_tiene_tiempo_maximo():
    async def lento(_):
        await asyncio.sleep(1)
        return respuesta_json()

    class Lento:
        name = "lento"

        async def complete(self, messages, *, temperature=0.2):
            return await lento(messages)

    rag = servicio(Lento(), llm_timeout=0.05)
    rag.index(Document("vacaciones", POLITICA))
    with pytest.raises(ProviderUnavailableError):
        await rag.answer("¿Cuántos días de vacaciones?")
