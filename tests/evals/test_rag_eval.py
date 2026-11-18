"""Sesión 13 — Evaluación de la recuperación con un 'golden set'.

Cada equipo amplía GOLDEN con 15-30 preguntas reales de su negocio.
Métrica: hit@k (¿el documento correcto está entre los k recuperados?).
Para evaluar la *generación* (fidelidad, alucinaciones), añadir un LLM-juez o ragas.
"""

import pytest

GOLDEN = [
    ("¿Cuántos días de vacaciones me corresponden?", "vacaciones"),
    ("¿Con cuánta anticipación pido vacaciones?", "vacaciones"),
    pytest.param(
        "¿En cuántos días legalizo los soportes del viaje?",
        "viáticos",
        # 'legalizo'≠'legalizan', 'viaje'≠'viajes': HashingEmbedding es léxico y falla aquí.
        # Taller sesión 10: cambiar a SentenceTransformerEmbedding y ver que esta prueba pasa.
        marks=pytest.mark.xfail(reason="límite de embeddings léxicos", strict=False),
    ),
    ("tope diario de alimentación en viajes nacionales", "viáticos"),
]


@pytest.mark.parametrize(("pregunta", "esperado"), GOLDEN)
def test_hit_at_k(rag, pregunta, esperado):
    textos = [c.text.lower() for c, _ in rag.retrieve(pregunta)]
    assert textos and esperado in textos[0], f"top-1 incorrecto para: {pregunta}"
