"""Sesiones 4, 5, 8 y 10: fábricas y envoltorios de proveedores."""

import time

import pytest

from asistente.adapters.embeddings.providers import (
    HashingEmbedding,
    SlowEmbedding,
    build_embedder,
)
from asistente.adapters.llm.providers import FakeLLM, build_llm
from asistente.domain.errors import ProviderUnavailableError, UnknownProviderError
from asistente.domain.models import Message, Role

HOLA = [Message(Role.USER, "hola")]


class Intermitente:
    name = "intermitente"

    def __init__(self, fallas, error=ProviderUnavailableError):
        self.fallas, self.error, self.llamadas = fallas, error, 0

    async def complete(self, messages, *, temperature=0.2):
        self.llamadas += 1
        if self.llamadas <= self.fallas:
            raise self.error("caído")
        return "ok"


def test_proveedor_desconocido_es_error_del_dominio():
    with pytest.raises(UnknownProviderError):
        build_llm("os.system")
    with pytest.raises(ValueError):  # también es ValueError, para quien lo atrape así
        build_llm("no-existe")


# taller: s04
async def test_proveedor_eco_registrado_sin_tocar_la_fabrica():
    import asistente.adapters.llm.eco  # noqa: F401

    llm = build_llm("ECO")
    respuesta = await llm.complete([Message(Role.SYSTEM, "s"), Message(Role.USER, "hola")])
    assert respuesta == "HOLA"


# taller: s05
def test_slow_embedding_espera_y_delega():
    lento = SlowEmbedding(HashingEmbedding(), delay=0.05)
    inicio = time.perf_counter()
    vectores = lento.embed(["a", "b"])
    assert time.perf_counter() - inicio >= 0.05
    assert vectores == HashingEmbedding().embed(["a", "b"]) and lento.dimensions == 512


def test_fabrica_de_embeddings():
    assert isinstance(build_embedder("hashing"), HashingEmbedding)
    with pytest.raises(UnknownProviderError):
        build_embedder("nada")


async def test_fake_llm_tambien_lee_imagenes():
    assert await FakeLLM(["texto leído"]).describe_image(b"x", "image/png", "lee") == "texto leído"
