"""Sesiones 2 y 4 — pruebas del dominio y del Unit of Work."""

import pytest

from asistente.adapters.embeddings.providers import HashingEmbedding
from asistente.adapters.persistence.memory import InMemoryStore, InMemoryUnitOfWork
from asistente.domain.models import Conversation, Document, Role


def test_split_respeta_tamano_y_solapamiento():
    doc = Document("t", "abcdefghij" * 10)  # 100 caracteres
    chunks = doc.split(size=40, overlap=10)
    assert all(len(c.text) <= 40 for c in chunks)
    assert chunks[0].text[-10:] == chunks[1].text[:10]
    assert "".join(c.text[:30] for c in chunks[:-1]) + chunks[-1].text == doc.content


def test_documento_vacio_no_genera_chunks():
    assert Document("t", "   ").split() == []


@pytest.mark.parametrize("overlap", [-1, 800, 900])
def test_overlap_invalido(overlap):
    with pytest.raises(ValueError):
        Document("t", "x").split(size=800, overlap=overlap)


def test_ventana_de_contexto_conserva_system_y_turnos_recientes():
    conv = Conversation(system_prompt="S")
    for i in range(10):
        conv.add(Role.USER, f"pregunta {i} " + "x" * 100)
    window = conv.window(max_chars=350)
    assert window[0].role is Role.SYSTEM
    assert window[-1].content.startswith("pregunta 9")
    assert len(window) < 11


# taller: s04
def test_unit_of_work_sin_commit_no_persiste():
    store = InMemoryStore()
    with InMemoryUnitOfWork(store) as uow:
        uow.documents.add(Document("t", "contenido"))
    assert store.documents == {}


# taller: s04
def test_unit_of_work_hace_rollback_si_hay_error():
    store = InMemoryStore()
    doc = Document("t", "contenido")
    with pytest.raises(ValueError), InMemoryUnitOfWork(store) as uow:
        uow.documents.add(doc)
        uow.chunks.add(doc.split())  # sin embeddings → ValueError
        uow.commit()
    assert store.documents == {}


# taller: s04
def test_unit_of_work_commit():
    store = InMemoryStore()
    doc = Document("t", "contenido")
    chunks = doc.split()
    for c, v in zip(chunks, HashingEmbedding().embed([c.text for c in chunks]), strict=True):
        c.embedding = v
    with InMemoryUnitOfWork(store) as uow:
        uow.documents.add(doc)
        uow.chunks.add(chunks)
        uow.commit()
    assert doc.id in store.documents and len(store.chunks) == 1
