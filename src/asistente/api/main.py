"""Sesiones 6, 7, 11 y 13: API REST asíncrona y versionada (adaptador de entrada del hexágono).

Ejecutar:  uv run --env-file .env uvicorn asistente.api.main:app --reload
Docs:      http://localhost:8000/docs   (se apagan con ENTORNO=produccion)
"""

from __future__ import annotations

import asyncio
import logging
import os
import tempfile
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, Request, UploadFile
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, ConfigDict, Field

import asistente.adapters.llm.eco  # noqa: F401  (registra el proveedor "eco", sesión 4)
from asistente.adapters.embeddings.providers import build_embedder
from asistente.adapters.llm.providers import LLMRefusalError, build_llm, build_vision
from asistente.adapters.llm.resilience import RetryingLLM
from asistente.adapters.persistence.memory import InMemoryStore, InMemoryUnitOfWork
from asistente.api.security import authenticate, create_token, groups_of, require_scope
from asistente.documents.extractors import default_extractors, load
from asistente.documents.uploads import MAX_BYTES, detectar_tipo
from asistente.domain.errors import (
    DocumentNotFoundError,
    EmptyDocumentError,
    FileTooLargeError,
    ProviderUnavailableError,
    UnsupportedFormatError,
)
from asistente.domain.models import Conversation, Document
from asistente.services.rag import SYSTEM_PROMPT, RagService
from asistente.services.structured import RespuestaRAG, StructuredOutputError

log = logging.getLogger(__name__)
PRODUCCION = os.getenv("ENTORNO", "desarrollo") == "produccion"
GRUPO = r"^[a-z0-9_-]{1,40}$"


# ------------------------------------------------------------ composición (raíz)
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """El único lugar que conoce las piezas concretas (sesión 5)."""
    store = InMemoryStore()
    app.state.rag = RagService(
        uow_factory=lambda: InMemoryUnitOfWork(store),
        embedder=build_embedder(),  # EMBEDDING_PROVIDER=hashing|ollama|sentence|openai
        llm=RetryingLLM(build_llm()),  # LLM_PROVIDER=fake|ollama|openai|anthropic|eco
        chunking="paragraphs" if os.getenv("CHUNKING") == "paragraphs" else "chars",
    )
    app.state.extractors = default_extractors(build_vision())
    # Clave (usuario, id): nadie continúa ni lee la conversación de otro conociendo su id.
    # En memoria y sin vencimiento solo para el curso; en producción, base de datos con TTL.
    app.state.conversations = {}
    yield


def get_rag(request: Request) -> RagService:
    return request.app.state.rag  # type: ignore[no-any-return]


# ------------------------------------------------------------ esquemas (DTO)
class DocumentIn(BaseModel):
    model_config = ConfigDict(extra="forbid")  # un campo desconocido es un error, no se ignora

    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=500_000)  # tope: sin él, una petición = DoS
    groups: list[Annotated[str, Field(pattern=GRUPO)]] = Field(
        default=["todos"], min_length=1, max_length=10
    )


class DocumentOut(BaseModel):
    id: UUID
    chunks: int


class DocumentInfo(BaseModel):
    id: UUID
    title: str
    source: str
    groups: list[str]


class AskIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=3, max_length=2000)
    conversation_id: UUID | None = None


class AskOut(RespuestaRAG):
    conversation_id: UUID


User = Annotated[dict[str, object], Depends(require_scope("docs:read"))]
Writer = Annotated[dict[str, object], Depends(require_scope("docs:write"))]
Rag = Annotated[RagService, Depends(get_rag)]


# ------------------------------------------------------------ rutas v1
v1 = APIRouter(prefix="/v1")


@v1.post("/token")
async def token(form: Annotated[OAuth2PasswordRequestForm, Depends()]) -> dict[str, str]:
    datos = authenticate(form.username, form.password)
    if datos is None:
        raise HTTPException(401, "Credenciales inválidas")
    scopes, grupos = datos
    return {"access_token": create_token(form.username, scopes, grupos), "token_type": "bearer"}


@v1.post("/documents", status_code=201)
async def add_document(body: DocumentIn, rag: Rag, _: Writer) -> DocumentOut:
    doc = Document(
        title=body.title, content=body.content, source="api", groups=frozenset(body.groups)
    )
    # index() es síncrono y calcula: en un hilo aparte para no bloquear el bucle de eventos
    chunks = await asyncio.to_thread(rag.index, doc)
    return DocumentOut(id=doc.id, chunks=chunks)


@v1.post("/documents/archivo", status_code=201)
async def upload_document(
    archivo: UploadFile, request: Request, rag: Rag, _: Writer
) -> DocumentOut:
    """Sesión 11: carga un PDF, una imagen o un texto, validado antes de procesarlo."""
    datos = await archivo.read(MAX_BYTES + 1)  # nunca se lee completo algo más grande
    extension = detectar_tipo(datos, archivo.filename or "")
    descriptor, nombre = tempfile.mkstemp(suffix=extension)  # nombre propio, permisos 0o600
    ruta = Path(nombre)
    try:
        with os.fdopen(descriptor, "wb") as f:
            f.write(datos)
        try:
            doc = await load(ruta, request.app.state.extractors)
        except ModuleNotFoundError:
            raise UnsupportedFormatError("faltan las librerías: uv sync --extra docs") from None
    finally:
        with suppress(FileNotFoundError):
            ruta.unlink()
    doc.title = Path(archivo.filename or doc.title).stem[:200]  # el nombre original, solo como dato
    chunks = await asyncio.to_thread(rag.index, doc)
    return DocumentOut(id=doc.id, chunks=chunks)


# taller: s06
@v1.get("/documents/{doc_id}")
async def get_document(doc_id: UUID, rag: Rag, user: User) -> DocumentInfo:
    """Datos de un documento; 404 si no existe o el usuario no puede verlo."""
    doc = rag.get_document(doc_id, groups=groups_of(user))
    return DocumentInfo(id=doc.id, title=doc.title, source=doc.source, groups=sorted(doc.groups))


@v1.post("/ask")
async def ask(body: AskIn, request: Request, rag: Rag, user: User) -> AskOut:
    convs: dict[tuple[str, UUID], Conversation] = request.app.state.conversations
    owner = str(user["sub"])
    conv = convs.get((owner, body.conversation_id)) if body.conversation_id else None
    if conv is None:  # inexistente o de otro usuario: se crea una nueva, sin revelar cuál
        conv = Conversation(system_prompt=SYSTEM_PROMPT)
        convs[(owner, conv.id)] = conv
    result = await rag.answer(body.question, conv, groups=groups_of(user))
    return AskOut(**result.model_dump(), conversation_id=conv.id)


@v1.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


# ------------------------------------------------------------ aplicación
app = FastAPI(
    title="Asistente documental con IA",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if PRODUCCION else "/docs",  # en producción no se publica el mapa de la API
    redoc_url=None,
    openapi_url=None if PRODUCCION else "/openapi.json",
)
if origenes := [o for o in os.getenv("CORS_ORIGINS", "").split(",") if o]:
    app.add_middleware(  # solo los sitios web listados pueden llamar a la API desde un navegador
        CORSMiddleware, allow_origins=origenes, allow_methods=["GET", "POST"], allow_headers=["*"]
    )
app.include_router(v1)


# ------------------------------------------------------------ errores del dominio → HTTP
def _json(status: int, detail: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"detail": detail})


# taller: s06
@app.exception_handler(DocumentNotFoundError)
async def no_encontrado(_: Request, exc: DocumentNotFoundError) -> JSONResponse:
    """Traduce el error del dominio a 404, en un solo lugar para toda la API."""
    return _json(404, f"No existe el documento {exc.args[0]}")


# taller: s06
@app.exception_handler(ProviderUnavailableError)
async def proveedor_caido(_: Request, exc: ProviderUnavailableError) -> JSONResponse:
    """Traduce el error del dominio a 503, con un mensaje que dice qué hacer."""
    return _json(503, "El modelo no está disponible. Intente de nuevo en unos segundos.")


@app.exception_handler(EmptyDocumentError)
async def vacio(_: Request, exc: EmptyDocumentError) -> JSONResponse:
    return _json(422, "El documento no tiene texto")


@app.exception_handler(UnsupportedFormatError)
async def formato(_: Request, exc: UnsupportedFormatError) -> JSONResponse:
    return _json(415, f"Formato no soportado: {exc}")


@app.exception_handler(FileTooLargeError)
async def grande(_: Request, exc: FileTooLargeError) -> JSONResponse:
    return _json(413, f"Archivo demasiado grande: {exc}")


@app.exception_handler(StructuredOutputError)
@app.exception_handler(LLMRefusalError)
async def respuesta_invalida(_: Request, exc: Exception) -> JSONResponse:
    log.warning("respuesta del modelo descartada: %s", type(exc).__name__)
    return _json(502, "El modelo no produjo una respuesta válida. Reformule la pregunta.")


@app.exception_handler(Exception)
async def inesperado(_: Request, exc: Exception) -> JSONResponse:
    log.exception("error no controlado")  # la traza va al log; al cliente, nada interno
    return _json(500, "Error interno")
