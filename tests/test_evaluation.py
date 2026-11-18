"""Sesión 13: el juez de la generación."""

from asistente.services.evaluation import Veredicto, resumir


def test_resumir_metricas():
    m = resumir([Veredicto(fiel=True, correcta=True), Veredicto(fiel=False, correcta=True)])
    assert (m.fidelidad, m.correccion, m.casos) == (0.5, 1.0, 2)
