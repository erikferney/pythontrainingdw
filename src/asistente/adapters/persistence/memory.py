"""Sesiones 4 y 13: Repository + Unit of Work en memoria.

Mismo contrato que tendría una versión con PostgreSQL/pgvector: los servicios no cambian.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from types import TracebackType
from typing import Self
from uuid import UUID

from asistente.domain.models import Chunk, Document


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


@dataclass
class InMemoryStore:
    """El 'motor de base de datos' compartido entre unidades de trabajo."""

    documents: dict[UUID, Document] = field(default_factory=dict)
    chunks: list[Chunk] = field(default_factory=list)


class InMemoryDocumentRepository:
    def __init__(self, store: InMemoryStore) -> None:
        self._store = store
        self.pending: list[Document] = []

    def add(self, doc: Document) -> None:
        self.pending.append(doc)

    def get(self, doc_id: UUID) -> Document | None:
        return self._store.documents.get(doc_id)

    def list(self) -> list[Document]:
        return list(self._store.documents.values())


class InMemoryVectorStore:
    def __init__(self, store: InMemoryStore) -> None:
        self._store = store
        self.pending: list[Chunk] = []

    def add(self, chunks: Sequence[Chunk]) -> None:
        if any(c.embedding is None for c in chunks):
            raise ValueError("Todos los chunks deben tener embedding antes de guardarse")
        self.pending.extend(chunks)

    # Sin marca de taller: el RAG la necesita desde la S5 (el filtro por grupos es de la S13).
    def search(
        self, vector: Sequence[float], k: int = 4, *, groups: frozenset[str]
    ) -> list[tuple[Chunk, float]]:
        """El permiso filtra ANTES de comparar vectores: así siempre llegan k visibles."""
        visibles = (c for c in self._store.chunks if c.groups & groups)
        scored = [(c, cosine(vector, c.embedding or [])) for c in visibles]
        return sorted(scored, key=lambda t: t[1], reverse=True)[:k]


class InMemoryUnitOfWork:
    def __init__(self, store: InMemoryStore | None = None) -> None:
        self.store = store or InMemoryStore()

    def __enter__(self) -> Self:
        self.documents = InMemoryDocumentRepository(self.store)
        self.chunks = InMemoryVectorStore(self.store)
        return self

    # taller: s04
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Al salir del bloque with: si no hubo commit explícito (o hubo excepción), se descarta."""
        raise NotImplementedError

    # taller: s04
    def commit(self) -> None:
        """Aplica de una vez todo lo pendiente y deja la unidad limpia."""
        raise NotImplementedError

    # taller: s04
    def rollback(self) -> None:
        """Descarta todo lo pendiente."""
        raise NotImplementedError
