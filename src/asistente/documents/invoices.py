"""Sesión 11: visión + salida estructurada. Extraer una factura y validar que cuadre."""

from __future__ import annotations

import json
import re
from datetime import date
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, Field, ValidationError, model_validator

from asistente.domain.ports import VisionProvider
from asistente.services.structured import StructuredOutputError

_JSON = re.compile(r"\{.*\}", re.DOTALL)


class Factura(BaseModel):
    nit_emisor: str = Field(pattern=r"^\d{6,10}-\d$", description="NIT con dígito de verificación")
    numero: str
    fecha: date
    subtotal: Decimal = Field(ge=0)
    iva: Decimal = Field(ge=0)
    total: Decimal = Field(ge=0)

    # taller: s11
    @model_validator(mode="after")
    def cuadra(self) -> Self:
        """Regla del negocio: subtotal + IVA debe dar el total (con un peso de tolerancia)."""
        raise NotImplementedError


async def extraer_factura(
    vision: VisionProvider, imagen: bytes, media_type: str, *, reintentos: int = 1
) -> Factura:
    """Pide los campos al modelo de visión y los valida; si no cuadran, le dice qué corregir."""
    esquema = json.dumps(Factura.model_json_schema(), ensure_ascii=False)
    prompt = f"Extrae los datos de esta factura. Responde solo un JSON con este esquema:\n{esquema}"
    error = ""
    for _ in range(reintentos + 1):
        crudo = await vision.describe_image(imagen, media_type, prompt)
        m = _JSON.search(crudo)
        try:
            return Factura.model_validate_json(m.group(0) if m else crudo)
        except ValidationError as e:
            error = str(e)
            prompt += f"\n\nTu respuesta anterior no era válida:\n{error}\nCorrígela."
    raise StructuredOutputError(error)
