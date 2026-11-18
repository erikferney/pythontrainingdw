"""Sesión 9: structured outputs agnósticos al proveedor, con validación y reintento.

Patrón: pedir JSON que cumpla un esquema Pydantic → validar → si falla, devolverle
al modelo el error de validación y pedirle que corrija (máx. N intentos).
Los SDKs ofrecen modos nativos (response_format / tool use); este patrón funciona con todos.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence

from pydantic import BaseModel, Field, ValidationError

from asistente.domain.errors import AssistantError
from asistente.domain.models import Message, Role
from asistente.domain.ports import LLMProvider

_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)


class Cita(BaseModel):
    fuente: int = Field(description="Número del fragmento citado, p. ej. 1 para [1]")
    extracto: str = Field(max_length=300)


class RespuestaRAG(BaseModel):
    respuesta: str
    citas: list[Cita] = Field(default_factory=list)
    confianza: float = Field(ge=0, le=1)
    requiere_humano: bool = False


class StructuredOutputError(AssistantError):
    """El modelo no produjo una salida válida ni después de los reintentos."""


async def complete_structured[T: BaseModel](
    llm: LLMProvider, messages: Sequence[Message], schema: type[T], *, retries: int = 2
) -> T:
    instruction = (
        "Responde ÚNICAMENTE con un objeto JSON válido que cumpla este JSON Schema, "
        f"sin texto adicional ni ```:\n{json.dumps(schema.model_json_schema(), ensure_ascii=False)}"
    )
    convo = [*messages, Message(Role.USER, instruction)]
    last_error = ""
    for _ in range(retries + 1):
        raw = await llm.complete(convo, temperature=0)
        match = _JSON_BLOCK.search(raw)
        try:
            return schema.model_validate_json(match.group(0) if match else raw)
        except ValidationError as e:
            last_error = str(e)
            convo += [
                Message(Role.ASSISTANT, raw),
                Message(
                    Role.USER,
                    f"El JSON no es válido:\n{last_error}\nCorrígelo y responde solo el JSON.",
                ),
            ]
    raise StructuredOutputError(last_error)
