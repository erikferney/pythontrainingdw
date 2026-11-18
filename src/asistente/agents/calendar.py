"""Sesión 12: festivos de Colombia y días hábiles.

Lo que se puede calcular de forma exacta se calcula con código y se le da al modelo como
herramienta: los modelos son malos con la aritmética de fechas y no conocen los festivos.

Reglas (Ley 51 de 1983, "Ley Emiliani"): algunos festivos son fijos; otros se trasladan al
lunes siguiente; y los religiosos móviles dependen del domingo de Pascua.
"""

from __future__ import annotations

from datetime import date, timedelta
from functools import cache

_FIJOS = [(1, 1), (5, 1), (7, 20), (8, 7), (12, 8), (12, 25)]
_AL_LUNES = [(1, 6), (3, 19), (6, 29), (8, 15), (10, 12), (11, 1), (11, 11)]
# Días después del domingo de Pascua; los marcados True se trasladan al lunes
_PASCUA = [(-3, False), (-2, False), (39, True), (60, True), (68, True)]


def pascua(anio: int) -> date:
    """Domingo de Pascua (algoritmo de Meeus/Jones/Butcher para el calendario gregoriano)."""
    a, b, c = anio % 19, anio // 100, anio % 100
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    m = (32 + 2 * e + 2 * i - h - k) % 7
    n = (a + 11 * h + 22 * m) // 451
    mes, dia = divmod(h + m - 7 * n + 114, 31)
    return date(anio, mes, dia + 1)


def _al_lunes(d: date) -> date:
    return d + timedelta(days=(7 - d.weekday()) % 7)


@cache
def festivos(anio: int) -> frozenset[date]:
    dias = {date(anio, m, d) for m, d in _FIJOS}
    dias |= {_al_lunes(date(anio, m, d)) for m, d in _AL_LUNES}
    p = pascua(anio)
    for delta, trasladar in _PASCUA:
        dia = p + timedelta(days=delta)
        dias.add(_al_lunes(dia) if trasladar else dia)
    return frozenset(dias)


def es_habil(d: date) -> bool:
    return d.weekday() < 5 and d not in festivos(d.year)


# taller: s12
def dias_habiles(desde: date, hasta: date) -> int:
    """Días hábiles entre dos fechas, ambas incluidas, sin fines de semana ni festivos."""
    raise NotImplementedError


def sumar_habiles(desde: date, dias: int) -> date:
    """La fecha en que se completan `dias` hábiles contando desde `desde` (incluida)."""
    if dias < 1:
        raise ValueError("dias debe ser al menos 1")
    d, contados = desde, 0
    while True:
        if es_habil(d):
            contados += 1
            if contados == dias:
                return d
        d += timedelta(days=1)
