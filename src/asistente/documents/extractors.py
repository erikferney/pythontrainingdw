"""Sesión 11: el puerto DocumentExtractor y sus adaptadores (cadena de responsabilidad).

Cada extractor dice qué archivos soporta y los convierte en un Document. Se usa el primero
de la lista que soporte el archivo; agregar Word es agregar un extractor.
"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from pathlib import Path

from asistente.documents.extract import extract_text
from asistente.domain.models import Document
from asistente.domain.ports import DocumentExtractor, VisionProvider

IMAGENES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
PROMPT_IMAGEN = (
    "Transcribe todo el texto de este documento en español, respetando el orden de lectura. "
    "Si hay tablas, escríbelas en Markdown. No agregues comentarios."
)


def _documento(path: Path, texto: str) -> Document:
    return Document(
        title=path.stem, content=texto, source=path.name, metadata={"tipo": path.suffix[1:]}
    )


class PlainTextExtractor:
    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in {".txt", ".md"}

    async def extract(self, path: Path) -> Document:
        return _documento(path, path.read_text(encoding="utf-8"))


class PdfExtractor:
    """Texto digital página por página; OCR solo en las páginas escaneadas (sesión 11)."""

    def __init__(self, ocr_lang: str = "spa") -> None:
        self.ocr_lang = ocr_lang

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() == ".pdf"

    async def extract(self, path: Path) -> Document:
        # PyMuPDF y Tesseract calculan: en un hilo aparte para no bloquear el bucle de eventos
        texto = await asyncio.to_thread(extract_text, path, self.ocr_lang)
        return _documento(path, texto)


class ImageExtractor:
    """Imágenes: OCR con Tesseract; si sale casi vacío, lo lee un modelo de visión."""

    def __init__(self, vision: VisionProvider | None = None, ocr_lang: str = "spa") -> None:
        self.vision = vision
        self.ocr_lang = ocr_lang

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in IMAGENES

    # taller: s11
    async def extract(self, path: Path) -> Document:
        """OCR primero (barato y local); el modelo de visión, solo si el OCR no alcanza."""
        raise NotImplementedError


def default_extractors(vision: VisionProvider | None = None) -> list[DocumentExtractor]:
    return [PlainTextExtractor(), PdfExtractor(), ImageExtractor(vision)]


# taller: s11
async def load(path: Path, extractors: Sequence[DocumentExtractor]) -> Document:
    """Usa el primer extractor que soporte el archivo; si ninguno, UnsupportedFormatError."""
    raise NotImplementedError
