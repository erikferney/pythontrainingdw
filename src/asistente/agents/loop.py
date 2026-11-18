"""Sesión 12 — Agente mínimo con herramientas, sin frameworks (para entender el ciclo).

Ciclo: el LLM decide → {"herramienta": ..., "argumentos": {...}} o {"final": "..."}
→ se ejecuta la herramienta → se le devuelve la observación → repetir (con tope de pasos).
Después de entenderlo, se puede migrar a tool use nativo del SDK o a LangGraph/PydanticAI.
"""

from __future__ import annotations

import inspect
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import BaseModel, ValidationError, validate_call

from asistente.domain.models import Message, Role
from asistente.domain.ports import LLMProvider

log = logging.getLogger(__name__)
ToolFn = Callable[..., Awaitable[str] | str]


class Decision(BaseModel):
    herramienta: str | None = None
    argumentos: dict[str, Any] = {}
    final: str | None = None


class Agent:
    def __init__(self, llm: LLMProvider, *, max_steps: int = 5) -> None:
        self.llm = llm
        self.max_steps = max_steps
        self.tools: dict[str, ToolFn] = {}
        self.trace: list[dict[str, Any]] = []

    def tool(self, fn: ToolFn) -> ToolFn:
        """Decorador para registrar herramientas; la docstring es su descripción.

        Los argumentos los propone el modelo: validate_call los verifica contra las
        anotaciones de tipo antes de ejecutar, como si vinieran de un desconocido.
        """
        self.tools[fn.__name__] = validate_call(fn)
        return fn

    def _system(self) -> str:
        catalog = "\n".join(
            f"- {name}{inspect.signature(fn)}: {inspect.getdoc(fn)}"
            for name, fn in self.tools.items()
        )
        return (
            "Eres un agente. Herramientas disponibles:\n" + catalog + "\n"
            'Responde SOLO JSON: {"herramienta": "nombre", "argumentos": {...}} '
            'o {"final": "respuesta para el usuario"}.'
        )

    async def run(self, task: str) -> str:
        messages = [Message(Role.SYSTEM, self._system()), Message(Role.USER, task)]
        for _ in range(self.max_steps):
            raw = await self.llm.complete(messages, temperature=0)
            try:
                decision = Decision.model_validate_json(raw)
            except ValidationError:
                messages += [
                    Message(Role.ASSISTANT, raw),
                    Message(Role.USER, "Formato inválido. Responde solo el JSON pedido."),
                ]
                continue
            if decision.final is not None:
                return decision.final
            fn = self.tools.get(decision.herramienta or "")
            if fn is None:
                observation = f"Error: la herramienta '{decision.herramienta}' no existe."
            else:
                name = decision.herramienta or ""
                observation = await self._execute(name, fn, decision.argumentos)
            self.trace.append(
                {"tool": decision.herramienta, "args": decision.argumentos, "obs": observation}
            )
            messages += [
                Message(Role.ASSISTANT, raw),
                Message(Role.USER, f"Observación: {json.dumps(observation, ensure_ascii=False)}"),
            ]
        return "No pude completar la tarea dentro del límite de pasos."

    @staticmethod
    async def _execute(name: str, fn: ToolFn, args: dict[str, Any]) -> str:
        try:
            out = fn(**args)
            return str(await out if inspect.isawaitable(out) else out)
        except ValidationError as e:  # el modelo puede corregir los argumentos
            detalles = "; ".join(f"{'.'.join(map(str, x['loc']))}: {x['msg']}" for x in e.errors())
            return f"Argumentos inválidos para {name}: {detalles}"
        except ValueError as e:  # errores pensados para el modelo: "use AAAA-MM-DD"
            return f"Error en {name}: {e}"
        except Exception:  # lo inesperado va al log; al modelo, sin detalles internos
            log.exception("falló la herramienta %s", name)
            return f"Error interno ejecutando {name}."
