"""Sesiones 4, 8 y 11: adaptadores de LLM (Strategy) + Factory.

- FakeLLM: respuestas programadas; permite probar TODO sin llaves ni costo.
- OpenAICompatibleLLM: sirve para OpenAI, Ollama (local), Groq, vLLM, LM Studio...
  cualquiera que exponga la API /v1/chat/completions.
- AnthropicLLM: SDK oficial de Anthropic (system prompt va aparte).

Los adaptadores traducen los errores transitorios de cada SDK (red, tiempo agotado, 429, 5xx)
a ProviderUnavailableError, del dominio: así el resto del sistema no conoce ningún SDK.
"""

from __future__ import annotations

import base64
import os
from collections.abc import Callable, Sequence
from itertools import cycle
from typing import Any, Literal

from asistente.domain.errors import AssistantError, ProviderUnavailableError, UnknownProviderError
from asistente.domain.models import Message, Role
from asistente.domain.ports import LLMProvider, VisionProvider


class LLMRefusalError(AssistantError):
    """El modelo (y su respaldo) declinó responder por sus políticas de seguridad."""


class FakeLLM:
    name = "fake"

    def __init__(
        self, replies: Sequence[str] | Callable[[Sequence[Message]], str] = ("ok",)
    ) -> None:
        self._fn = replies if callable(replies) else None
        self._replies = cycle(replies) if not callable(replies) else None
        self.calls: list[list[Message]] = []

    async def complete(self, messages: Sequence[Message], *, temperature: float = 0.2) -> str:
        self.calls.append(list(messages))
        if self._fn:
            return self._fn(messages)
        if self._replies is None:
            raise RuntimeError("FakeLLM sin respuestas configuradas")
        return next(self._replies)

    async def describe_image(self, image: bytes, media_type: str, prompt: str) -> str:
        """Para probar la sesión 11 sin modelo de visión: responde como si leyera la imagen."""
        return await self.complete([Message(Role.USER, prompt)])


def _openai_transient(e: Exception) -> bool:
    import openai

    return isinstance(
        e, openai.APIConnectionError | openai.RateLimitError | openai.InternalServerError
    )


class OpenAICompatibleLLM:
    def __init__(
        self,
        model: str,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        name: str = "openai",
        reasoning_effort: str | None = None,
        timeout: float = 60,
    ) -> None:
        from openai import AsyncOpenAI

        self.name = name
        self._model = model
        # Modelos que razonan (qwen3, gpt-oss): "none" responde en segundos en vez de decenas;
        # "low"/"medium"/"high" piensan más. None = lo que decida el modelo.
        self._extra = {"reasoning_effort": reasoning_effort} if reasoning_effort else None
        # Tiempo máximo explícito; los reintentos con espera los controla RetryingLLM (sesión 8).
        self._client = AsyncOpenAI(
            base_url=base_url, api_key=api_key, timeout=timeout, max_retries=0
        )

    async def _chat(self, messages: list[dict[str, Any]], temperature: float) -> str:
        try:
            resp = await self._client.chat.completions.create(
                model=self._model,
                temperature=temperature,
                messages=messages,  # type: ignore[arg-type]
                extra_body=self._extra,
            )
        except Exception as e:
            if _openai_transient(e):
                raise ProviderUnavailableError(
                    f"{self.name} no disponible: {type(e).__name__}"
                ) from e
            raise
        return resp.choices[0].message.content or ""

    async def complete(self, messages: Sequence[Message], *, temperature: float = 0.2) -> str:
        return await self._chat(
            [{"role": m.role.value, "content": m.content} for m in messages], temperature
        )

    async def describe_image(self, image: bytes, media_type: str, prompt: str) -> str:
        """Sesión 11: imagen y texto en un mensaje; en esta API la imagen va como data URL."""
        data_url = f"data:{media_type};base64,{base64.b64encode(image).decode()}"
        contenido = [
            {"type": "image_url", "image_url": {"url": data_url}},
            {"type": "text", "text": prompt},
        ]
        return await self._chat([{"role": "user", "content": contenido}], temperature=0)


Effort = Literal["low", "medium", "high", "xhigh", "max"]


def _anthropic_transient(e: Exception) -> bool:
    import anthropic

    return isinstance(
        e, anthropic.APIConnectionError | anthropic.RateLimitError | anthropic.InternalServerError
    )


class AnthropicLLM:
    """Claude por el SDK oficial de Anthropic.

    En los modelos actuales (Claude Opus 5.5, Claude Sonnet 5.5) los parámetros de muestreo
    como `temperature` ya no existen: enviarlos devuelve un 400. La profundidad del razonamiento
    se controla con `effort`. Si el modelo declina por sus políticas, el servidor reintenta en
    la misma llamada con un modelo de respaldo (`fallbacks="default"`).
    """

    name = "anthropic"
    _BETAS = ["server-side-fallback-2026-07-01"]

    def __init__(
        self,
        model: str,
        *,
        api_key: str | None = None,
        max_tokens: int = 16000,
        effort: Effort = "medium",
        timeout: float = 120,
    ) -> None:
        from anthropic import AsyncAnthropic

        self._model = model
        self._max_tokens = max_tokens
        self._effort: Effort = effort
        self._client = AsyncAnthropic(api_key=api_key, timeout=timeout, max_retries=0)

    async def _crear(self, **kwargs: Any) -> str:
        try:
            resp = await self._client.beta.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                output_config={"effort": self._effort},
                betas=self._BETAS,
                fallbacks="default",
                **kwargs,
            )
        except Exception as e:
            if _anthropic_transient(e):
                raise ProviderUnavailableError(
                    f"anthropic no disponible: {type(e).__name__}"
                ) from e
            raise
        if resp.stop_reason == "refusal":
            categoria = resp.stop_details.category if resp.stop_details else None
            raise LLMRefusalError(f"El modelo declinó responder (categoría: {categoria})")
        return "".join(b.text for b in resp.content if b.type == "text")

    async def complete(self, messages: Sequence[Message], *, temperature: float = 0.2) -> str:
        # `temperature` llega por el puerto LLMProvider; Claude ya no la acepta y se ignora.
        system = "\n".join(m.content for m in messages if m.role is Role.SYSTEM)
        turns = [
            {"role": m.role.value, "content": m.content}
            for m in messages
            if m.role is not Role.SYSTEM
        ]
        return await self._crear(system=system, messages=turns)

    async def describe_image(self, image: bytes, media_type: str, prompt: str) -> str:
        """Sesión 11: caso multimodal, imagen y texto en el mismo mensaje."""
        imagen = {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": base64.b64encode(image).decode(),
            },
        }
        contenido = [imagen, {"type": "text", "text": prompt}]
        return await self._crear(messages=[{"role": "user", "content": contenido}])


# ---------------------------------------------------------------- Factory (sesión 4)
def _ollama(model_env: str, default: str) -> OpenAICompatibleLLM:
    return OpenAICompatibleLLM(
        os.getenv(model_env, default),
        base_url=os.getenv("OLLAMA_URL", "http://localhost:11434/v1"),
        api_key="ollama",
        name="ollama",
        reasoning_effort=os.getenv("OLLAMA_REASONING", "none") or None,
    )


_REGISTRY: dict[str, Callable[[], LLMProvider]] = {
    "fake": lambda: FakeLLM(),
    "openai": lambda: OpenAICompatibleLLM(os.environ["OPENAI_MODEL"]),
    "ollama": lambda: _ollama("OLLAMA_MODEL", "qwen3:14b"),
    "anthropic": lambda: AnthropicLLM(os.environ["ANTHROPIC_MODEL"]),
}

_VISION: dict[str, Callable[[], VisionProvider]] = {
    "fake": lambda: FakeLLM(),
    "ollama": lambda: _ollama("OLLAMA_VISION_MODEL", "qwen2.5vl:7b"),
    "anthropic": lambda: AnthropicLLM(os.environ["ANTHROPIC_MODEL"]),
}


def build_llm(provider: str | None = None) -> LLMProvider:
    """Construye el proveedor que diga `provider` o LLM_PROVIDER (por defecto, el falso).

    Solo se aceptan nombres registrados: lo demás es UnknownProviderError (lista de permitidos).
    """
    key = (provider or os.environ.get("LLM_PROVIDER") or "fake").lower()
    try:
        factory = _REGISTRY[key]
    except KeyError:
        raise UnknownProviderError(
            f"Proveedor no soportado: {key}. Opciones: {sorted(_REGISTRY)}"
        ) from None
    return factory()


def build_vision(provider: str | None = None) -> VisionProvider:
    """Sesión 11: proveedor con visión según VISION_PROVIDER (o el de LLM_PROVIDER)."""
    key = (provider or os.getenv("VISION_PROVIDER") or os.getenv("LLM_PROVIDER") or "fake").lower()
    try:
        factory = _VISION[key]
    except KeyError:
        raise UnknownProviderError(f"Sin visión para {key}. Opciones: {sorted(_VISION)}") from None
    return factory()


def register_llm(key: str, factory: Callable[[], LLMProvider]) -> None:
    """Abierto a extensión, cerrado a modificación (OCP): un proveedor nuevo se registra solo."""
    clave = key.lower()
    if clave in _REGISTRY:
        raise ValueError(f"Ya hay un proveedor registrado como {clave!r}")
    _REGISTRY[clave] = factory
