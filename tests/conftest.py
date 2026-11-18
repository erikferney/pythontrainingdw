import json

import pytest

from asistente.adapters.embeddings.providers import HashingEmbedding
from asistente.adapters.llm.providers import FakeLLM
from asistente.adapters.persistence.memory import InMemoryStore, InMemoryUnitOfWork
from asistente.services.rag import RagService

POLITICA = (
    "Política de vacaciones. Los empleados tienen derecho a 15 días hábiles de vacaciones "
    "por cada año de servicio. Las vacaciones se solicitan con 30 días de anticipación "
    "a través del portal de talento humano."
)
VIATICOS = (
    "Política de viáticos. Los viajes nacionales tienen un tope diario de alimentación. "
    "Los soportes se legalizan dentro de los 5 días siguientes al regreso."
)


def respuesta_json(texto: str = "15 días hábiles [1]", fuente: int = 1) -> str:
    return json.dumps(
        {
            "respuesta": texto,
            "citas": [{"fuente": fuente, "extracto": "15 días"}],
            "confianza": 0.9,
            "requiere_humano": False,
        }
    )


@pytest.fixture
def store() -> InMemoryStore:
    return InMemoryStore()


@pytest.fixture
def rag(store: InMemoryStore) -> RagService:
    svc = RagService(
        lambda: InMemoryUnitOfWork(store), HashingEmbedding(), FakeLLM([respuesta_json()])
    )
    from asistente.domain.models import Document

    svc.index(Document("vacaciones", POLITICA))
    svc.index(Document("viaticos", VIATICOS))
    return svc
