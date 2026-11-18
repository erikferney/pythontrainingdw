"""Sesión 5: el experimento del taller. ¿Hilos o procesos? Depende de dónde se va el tiempo.

    uv run python scripts/medir_ingesta.py            # 200 documentos de 20 000 caracteres
    uv run python scripts/medir_ingesta.py --docs 40  # versión rápida

Imprime la tabla en Markdown, lista para pegar en el README del Pull Request.
"""

from __future__ import annotations

import argparse
import random
import string
import time
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

from asistente.adapters.embeddings.providers import HashingEmbedding, SlowEmbedding
from asistente.adapters.persistence.memory import InMemoryStore, InMemoryUnitOfWork
from asistente.domain.models import Document
from asistente.domain.ports import EmbeddingProvider
from asistente.services.ingestion import ingest_batch


def documentos(n: int, largo: int, semilla: int = 7) -> list[Document]:
    azar = random.Random(semilla)  # noqa: S311 (datos de prueba, no seguridad)
    palabras = [
        "".join(azar.choices(string.ascii_lowercase, k=azar.randint(3, 9))) for _ in range(2000)
    ]
    return [
        Document(f"doc-{i}", " ".join(azar.choices(palabras, k=largo // 6))[:largo])
        for i in range(n)
    ]


def medir(fn: Callable[[], object]) -> float:
    inicio = time.perf_counter()
    fn()
    return time.perf_counter() - inicio


def experimento(docs: list[Document], embedder: EmbeddingProvider) -> dict[str, float]:
    def con(executor: object) -> Callable[[], object]:
        store = InMemoryStore()
        return lambda: ingest_batch(
            docs,
            embedder,
            lambda: InMemoryUnitOfWork(store),
            executor=executor,  # type: ignore[arg-type]
        )

    return {
        "secuencial": medir(con(ThreadPoolExecutor(max_workers=1))),
        "8 hilos": medir(con(ThreadPoolExecutor(max_workers=8))),
        "8 procesos": medir(con(ProcessPoolExecutor(max_workers=8))),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--docs", type=int, default=200)
    p.add_argument("--largo", type=int, default=20_000)
    p.add_argument("--espera", type=float, default=0.2, help="latencia simulada por llamada")
    a = p.parse_args()
    docs = documentos(a.docs, a.largo)
    cargas = {
        "Cálculo puro (hashing)": HashingEmbedding(),
        f"Espera de red ({a.espera} s)": SlowEmbedding(HashingEmbedding(), a.espera),
    }
    print(f"{a.docs} documentos de {a.largo} caracteres\n")
    print("| Carga | Secuencial | 8 hilos | 8 procesos |\n|---|---|---|---|")
    for nombre, embedder in cargas.items():
        t = experimento(docs, embedder)
        base = t["secuencial"]
        celdas = " | ".join(f"{s:.2f} s ({base / s:.1f}×)" for s in t.values())
        print(f"| {nombre} | {celdas} |")


if __name__ == "__main__":  # obligatorio en Mac: ProcessPoolExecutor arranca con spawn
    main()
