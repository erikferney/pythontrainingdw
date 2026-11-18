"""Sesiones 6, 9, 10 y 13: pipeline RAG. Indexar → recuperar → generar con citas.

Junta casi todo el curso: puertos (5), unidad de trabajo (4), salida estructurada (9),
fragmentos delimitados y sin datos sensibles (13), tiempo máximo (6) y control de acceso
por grupos en la búsqueda (13).
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from uuid import UUID

from asistente.domain.errors import DocumentNotFoundError, ProviderUnavailableError
from asistente.domain.models import PUBLIC, Chunk, Conversation, Document, Message, Role
from asistente.domain.ports import EmbeddingProvider, LLMProvider, UnitOfWork
from asistente.services.guardrails import looks_like_injection, redact, wrap_untrusted
from asistente.services.indexing import Chunking, IndexingService
from asistente.services.structured import RespuestaRAG, complete_structured

SYSTEM_PROMPT = (
    "Eres un asistente que responde preguntas sobre documentos de la empresa. "
    "Usa SOLO el contexto entregado. Cita los fragmentos como [n]. "
    "Si el contexto no alcanza, dilo, pon confianza baja y requiere_humano=true."
)
SIN_INFORMACION = "No encontré información en los documentos."


@dataclass
class RagService:
    uow_factory: Callable[[], UnitOfWork]
    embedder: EmbeddingProvider
    llm: LLMProvider
    k: int = 4
    min_score: float = 0.05
    llm_timeout: float = 60
    chunking: Chunking = "chars"
    _indexer: IndexingService = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._indexer = IndexingService(self.embedder, self.uow_factory, self.chunking)

    def index(self, doc: Document) -> int:
        return self._indexer.index(doc)

    def get_document(self, doc_id: UUID, *, groups: frozenset[str] = PUBLIC) -> Document:
        """Sesión 6: el documento, si existe y el usuario puede verlo (si no, no existe para él)."""
        with self.uow_factory() as uow:
            doc = uow.documents.get(doc_id)
        if doc is None or not doc.groups & groups:
            raise DocumentNotFoundError(str(doc_id))
        return doc

    def retrieve(
        self, question: str, *, groups: frozenset[str] = PUBLIC
    ) -> list[tuple[Chunk, float]]:
        """Los fragmentos más parecidos que el usuario puede ver, sin los sospechosos de inyección.

        Por defecto solo lo público: quien olvide pasar los grupos ve menos, nunca más.
        """
        [qvec] = self.embedder.embed([question])
        with self.uow_factory() as uow:
            hits = uow.chunks.search(qvec, self.k, groups=groups)
        return [(c, s) for c, s in hits if s >= self.min_score and not looks_like_injection(c.text)]

    async def answer(
        self,
        question: str,
        conversation: Conversation | None = None,
        *,
        groups: frozenset[str] = PUBLIC,
    ) -> RespuestaRAG:
        hits = self.retrieve(question, groups=groups)
        if not hits:  # sin contexto ni siquiera se llama al modelo: ni costo ni invención
            return RespuestaRAG(respuesta=SIN_INFORMACION, confianza=0.0, requiere_humano=True)
        conversation = conversation or Conversation(system_prompt=SYSTEM_PROMPT)
        context = wrap_untrusted([redact(c.text) for c, _ in hits])
        messages = [
            *conversation.window(),
            Message(Role.USER, f"{context}\n\nPregunta: {question}"),
        ]
        try:
            async with asyncio.timeout(self.llm_timeout):
                result = await complete_structured(self.llm, messages, RespuestaRAG)
        except TimeoutError as e:
            raise ProviderUnavailableError(f"sin respuesta en {self.llm_timeout} s") from e
        self._aplicar_reglas(result, len(hits))
        conversation.add(Role.USER, question)
        conversation.add(Role.ASSISTANT, result.respuesta)
        return result

    # taller: s09
    @staticmethod
    def _aplicar_reglas(result: RespuestaRAG, fragmentos: int) -> None:
        """Reglas del negocio después de validar la forma (control de alucinaciones).

        Solo se aceptan citas a fragmentos entregados; sin citas válidas, la confianza no pasa
        de 0.5 y se escala a una persona.
        """
        raise NotImplementedError
