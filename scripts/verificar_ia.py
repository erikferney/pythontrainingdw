"""Verifica que Ollama y los modelos del curso estén listos. Se corre desde la raíz del repositorio:

    uv run --env-file .env python scripts/verificar_ia.py

Lee OLLAMA_URL, OLLAMA_MODEL y OLLAMA_EMBED_MODEL del .env (ver INSTALACION.md). No envía nada
fuera de su equipo: solo habla con el Ollama local.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
import urllib.request
from typing import NoReturn

from asistente.adapters.llm.providers import build_llm
from asistente.domain.models import Message, Role

URL = os.getenv("OLLAMA_URL", "http://localhost:11434/v1")
CHAT = os.getenv("OLLAMA_MODEL", "")
EMBED = os.getenv("OLLAMA_EMBED_MODEL", "qwen3-embedding:0.6b")


def ok(texto: str) -> None:
    print(f"  ✓ {texto}")


def falla(texto: str, pista: str) -> NoReturn:
    print(f"  ✗ {texto}\n    → {pista}")
    sys.exit(1)


def modelos_instalados() -> set[str]:
    with urllib.request.urlopen(f"{URL}/models", timeout=5) as r:  # noqa: S310 (URL local)
        return {m["id"] for m in json.load(r)["data"]}


def embeddings(textos: list[str]) -> list[list[float]]:
    """Directo a Ollama: el adaptador del kit (OllamaEmbedding) es el taller de la clase 3."""
    datos = json.dumps({"model": EMBED, "input": textos}).encode()
    pedido = urllib.request.Request(  # noqa: S310 (URL local)
        f"{URL}/embeddings", data=datos, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(pedido, timeout=120) as r:  # noqa: S310 (URL local)
        return [d["embedding"] for d in json.load(r)["data"]]


async def main() -> None:
    print("1. Ollama")
    try:
        instalados = modelos_instalados()
    except OSError:
        falla(
            f"No responde en {URL}",
            "Abra la aplicación Ollama (en Linux: `ollama serve`) y vuelva a intentar.",
        )
    ok(f"responde en {URL} con {len(instalados)} modelo(s)")

    print("2. Modelos")
    if not CHAT:
        falla("OLLAMA_MODEL está vacío", "¿Creó el .env y corrió con `--env-file .env`?")
    for modelo in (CHAT, EMBED):
        if modelo not in instalados:
            falla(f"Falta {modelo}", f"ollama pull {modelo}   (instalados: {sorted(instalados)})")
        ok(modelo)

    print(f"3. Chat con {CHAT} (la primera vez carga el modelo: puede tardar hasta un minuto)")
    try:
        llm = build_llm("ollama")
    except ModuleNotFoundError:
        falla("Falta el paquete openai", "uv sync --extra llm --extra docs")
    inicio = time.perf_counter()
    respuesta = await llm.complete(
        [
            Message(Role.SYSTEM, "Responde en español, en una sola frase corta."),
            Message(Role.USER, "¿Cuál es la capital de Colombia?"),
        ]
    )
    ok(f"{respuesta.strip()[:80]!r} en {time.perf_counter() - inicio:.1f} s")

    print(f"4. Embeddings con {EMBED}")
    vectores = embeddings(["vacaciones", "días de descanso"])
    ok(f"{len(vectores)} vectores de {len(vectores[0])} dimensiones")

    print("\nTodo listo para las clases de IA.")


if __name__ == "__main__":
    asyncio.run(main())
