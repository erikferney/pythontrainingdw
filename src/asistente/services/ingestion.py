"""Sesiones 5 y 6: ingesta concurrente de un lote de documentos.

Idea clave para el taller:
- Embeddings por API = I/O-bound  → hilos (ThreadPoolExecutor) o asyncio.
- Embeddings locales / OCR / parsing pesado = CPU-bound → procesos (ProcessPoolExecutor),
  porque el GIL impide que los hilos usen varios núcleos en código Python puro.
"""

from __future__ import annotations

import asyncio
import functools
from collections.abc import Callable, Sequence
from concurrent.futures import Executor, ProcessPoolExecutor, ThreadPoolExecutor

from asistente.domain.models import Chunk, Document
from asistente.domain.ports import EmbeddingProvider, UnitOfWork


def _split(doc: Document) -> list[Chunk]:
    # Función de nivel de módulo: debe ser 'picklable' para ProcessPoolExecutor.
    return doc.split()


def _embed_doc(embedder: EmbeddingProvider, doc: Document) -> tuple[Document, list[Chunk]]:
    chunks = _split(doc)
    for chunk, vec in zip(chunks, embedder.embed([c.text for c in chunks]), strict=True):
        chunk.embedding = vec
    return doc, chunks


def ingest_batch(
    docs: Sequence[Document],
    embedder: EmbeddingProvider,
    uow_factory: Callable[[], UnitOfWork],
    *,
    executor: Executor | None = None,
) -> int:
    """Vectoriza en paralelo y persiste en una sola transacción. Devuelve # de chunks."""
    executor = executor or ThreadPoolExecutor(max_workers=8)
    with executor:
        # partial y no lambda: con procesos, la función viaja serializada (pickle)
        results = list(executor.map(functools.partial(_embed_doc, embedder), docs))
    with uow_factory() as uow:
        for doc, chunks in results:
            uow.documents.add(doc)
            uow.chunks.add(chunks)
        uow.commit()
    return sum(len(c) for _, c in results)


def split_with_processes(docs: Sequence[Document], workers: int = 4) -> list[list[Chunk]]:
    """Demostración CPU-bound: compárelo con time.perf_counter() contra la versión con hilos."""
    with ProcessPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(_split, docs))


async def ingest_async(
    docs: Sequence[Document],
    embedder: EmbeddingProvider,
    uow_factory: Callable[[], UnitOfWork],
    *,
    max_concurrency: int = 5,
) -> int:
    """Versión asyncio (sesión 6) con semáforo para no saturar el rate limit del proveedor."""
    sem = asyncio.Semaphore(max_concurrency)

    async def one(doc: Document) -> tuple[Document, list[Chunk]]:
        async with sem:
            return await asyncio.to_thread(_embed_doc, embedder, doc)

    results = await asyncio.gather(*(one(d) for d in docs))
    with uow_factory() as uow:
        for doc, chunks in results:
            uow.documents.add(doc)
            uow.chunks.add(chunks)
        uow.commit()
    return sum(len(c) for _, c in results)
