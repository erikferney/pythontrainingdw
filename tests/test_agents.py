"""Sesión 12: calendario, herramientas con permisos y enrutamiento."""

import json
from datetime import date

import pytest
from conftest import POLITICA

from asistente.adapters.embeddings.providers import HashingEmbedding
from asistente.adapters.llm.providers import FakeLLM
from asistente.adapters.persistence.memory import InMemoryStore, InMemoryUnitOfWork
from asistente.agents.calendar import festivos, pascua
from asistente.agents.loop import Agent
from asistente.agents.tools import Solicitudes, Usuario, registrar_herramientas, usuario_actual
from asistente.domain.models import Document
from asistente.services.rag import RagService

ANALISTA = Usuario("analista", frozenset({"docs:read", "solicitudes:crear"}))
INVITADO = Usuario("invitado")


def test_pascua_y_festivos_de_colombia_2026():
    assert pascua(2026) == date(2026, 4, 5)
    f = festivos(2026)
    for d in [
        date(2026, 1, 12),  # Reyes, trasladado al lunes
        date(2026, 3, 23),  # San José, trasladado
        date(2026, 4, 2),  # Jueves Santo
        date(2026, 4, 3),  # Viernes Santo
        date(2026, 5, 18),  # Ascensión
        date(2026, 6, 8),  # Corpus Christi
        date(2026, 6, 15),  # Sagrado Corazón
        date(2026, 8, 17),  # Asunción, trasladada
        date(2026, 11, 2),  # Todos los Santos, trasladado
        date(2026, 11, 16),  # Independencia de Cartagena, trasladada
        date(2026, 12, 25),
    ]:
        assert d in f, d
    assert len(f) == 18


@pytest.fixture
def herramientas():
    store = InMemoryStore()
    rag = RagService(lambda: InMemoryUnitOfWork(store), HashingEmbedding(), FakeLLM())
    rag.index(Document("vacaciones", POLITICA))
    agent, solicitudes = Agent(FakeLLM()), Solicitudes()
    registrar_herramientas(agent, rag, solicitudes)
    return agent, solicitudes, rag


async def test_el_agente_usa_las_herramientas_con_el_usuario_actual(herramientas):
    _, _, rag = herramientas
    llm = FakeLLM(
        [
            json.dumps(
                {"herramienta": "buscar_documentos", "argumentos": {"pregunta": "vacaciones"}}
            ),
            json.dumps(
                {
                    "herramienta": "fecha_tras_dias_habiles",
                    "argumentos": {"desde": "2026-12-14", "dias": 15},
                }
            ),
            json.dumps({"final": "Regresa el 6 de enero [1]."}),
        ]
    )
    agent = Agent(llm, max_steps=4)
    registrar_herramientas(agent, rag, Solicitudes())
    token = usuario_actual.set(ANALISTA)
    try:
        assert await agent.run("¿Cuándo vuelvo si salgo el 14 de diciembre?") == (
            "Regresa el 6 de enero [1]."
        )
    finally:
        usuario_actual.reset(token)
    assert "[1]" in agent.trace[0]["obs"] and agent.trace[1]["obs"] == "2027-01-05"
