"""Sesiones 3, 4 y 10: el caso de uso de indexación."""

import pytest

from asistente.adapters.embeddings.providers import HashingEmbedding
from asistente.adapters.persistence.memory import InMemoryStore, InMemoryUnitOfWork
from asistente.domain.errors import AssistantError, EmptyDocumentError
from asistente.domain.models import Document
from asistente.services.indexing import IndexingService

TEXTO = "Política de vacaciones. " * 60  # unos 1 400 caracteres


class EmbeddingQueSeQuedaCorto:
    dimensions = 3

    def embed(self, texts):
        return [[1.0, 0.0, 0.0]]  # siempre uno, aunque le pidan varios


# taller: s03
def test_vectorize_asigna_un_vector_a_cada_fragmento():
    chunks = IndexingService(HashingEmbedding()).vectorize(Document("t", TEXTO))
    assert len(chunks) > 1
    assert all(c.embedding and len(c.embedding) == 512 for c in chunks)


# taller: s03
def test_documento_vacio_es_un_error_del_dominio():
    with pytest.raises(EmptyDocumentError):
        IndexingService(HashingEmbedding()).vectorize(Document("t", "   "))
    assert issubclass(EmptyDocumentError, AssistantError)


# taller: s03
def test_si_faltan_vectores_falla_en_vez_de_callar():
    with pytest.raises(ValueError):
        IndexingService(EmbeddingQueSeQuedaCorto()).vectorize(Document("t", TEXTO))


# taller: s04
def test_index_guarda_documento_y_fragmentos_juntos():
    store = InMemoryStore()
    svc = IndexingService(HashingEmbedding(), lambda: InMemoryUnitOfWork(store))
    doc = Document("t", TEXTO)
    n = svc.index(doc)
    assert doc.id in store.documents and len(store.chunks) == n > 1


# taller: s04
def test_si_la_vectorizacion_falla_no_queda_nada_guardado():
    store = InMemoryStore()
    svc = IndexingService(EmbeddingQueSeQuedaCorto(), lambda: InMemoryUnitOfWork(store))
    with pytest.raises(ValueError):
        svc.index(Document("t", TEXTO))
    assert store.documents == {} and store.chunks == []
