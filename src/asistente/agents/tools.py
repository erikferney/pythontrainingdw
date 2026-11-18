"""Sesión 12: herramientas del agente, con los permisos del usuario que pidió la tarea.

- usuario_actual: variable de contexto que la API fija al recibir la petición; cada petición
  concurrente ve la suya (contextvars).
- Las herramientas que leen se ejecutan; las que escriben dejan la acción PENDIENTE y es la
  persona quien la confirma.
"""

from __future__ import annotations

import contextvars
from dataclasses import dataclass, field
from datetime import date
from typing import Literal
from uuid import UUID, uuid4

from asistente.agents import calendar
from asistente.agents.loop import Agent
from asistente.domain.models import PUBLIC
from asistente.services.rag import RagService


@dataclass(frozen=True)
class Usuario:
    id: str
    permisos: frozenset[str] = frozenset()
    grupos: frozenset[str] = PUBLIC


usuario_actual: contextvars.ContextVar[Usuario] = contextvars.ContextVar("usuario_actual")

# Nómina simulada: en una empresa real sería un adaptador hacia su sistema de nómina
SALDOS_VACACIONES: dict[str, int] = {"analista": 12, "admin": 20}

TipoSolicitud = Literal["certificado_laboral", "vacaciones"]


@dataclass
class Pendiente:
    usuario: str
    tipo: TipoSolicitud
    fecha: date
    id: UUID = field(default_factory=uuid4)

    def resumen(self) -> str:
        return f"{self.tipo} para el {self.fecha.isoformat()} (id {self.id})"


@dataclass
class Solicitudes:
    """Acciones que esperan la confirmación de una persona, y las ya radicadas."""

    pendientes: dict[UUID, Pendiente] = field(default_factory=dict)
    radicadas: list[Pendiente] = field(default_factory=list)

    def confirmar(self, pendiente_id: UUID, usuario: Usuario) -> Pendiente:
        p = self.pendientes.get(pendiente_id)
        if p is None or p.usuario != usuario.id:  # solo el dueño confirma lo suyo
            raise PermissionError("No hay una solicitud pendiente con ese id para este usuario")
        del self.pendientes[pendiente_id]
        self.radicadas.append(p)
        return p


def registrar_herramientas(agent: Agent, rag: RagService, solicitudes: Solicitudes) -> None:
    """Registra las herramientas del asistente en el agente (la docstring es la descripción)."""

    @agent.tool
    def buscar_documentos(pregunta: str) -> str:
        """Busca en las políticas de la empresa. Devuelve fragmentos numerados."""
        hits = rag.retrieve(pregunta, groups=usuario_actual.get().grupos)
        if not hits:
            return "No se encontraron documentos sobre eso."
        return "\n".join(f"[{i}] {c.text[:400]}" for i, (c, _) in enumerate(hits, 1))

    @agent.tool
    def dias_habiles(desde: date, hasta: date) -> str:
        """Días hábiles entre dos fechas AAAA-MM-DD, ambas incluidas, con festivos de Colombia."""
        return str(calendar.dias_habiles(desde, hasta))

    @agent.tool
    def fecha_tras_dias_habiles(desde: date, dias: int) -> str:
        """Fecha AAAA-MM-DD en que se completan `dias` hábiles contando desde `desde`."""
        return calendar.sumar_habiles(desde, dias).isoformat()

    # taller: s12
    @agent.tool
    def saldo_vacaciones() -> str:
        """Días de vacaciones pendientes del usuario que pregunta."""
        raise NotImplementedError

    # taller: s12
    @agent.tool
    def radicar_solicitud(tipo: TipoSolicitud, fecha: date) -> str:
        """Prepara una solicitud de certificado laboral o de vacaciones para una fecha.

        No la radica: queda pendiente hasta que el usuario la confirme.
        """
        raise NotImplementedError
