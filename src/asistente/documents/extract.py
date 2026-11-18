"""Sesión 11 — Extracción de texto: PDF digital, PDF escaneado (OCR) e imágenes.

Requiere: uv sync --extra docs  y Tesseract instalado en el sistema
(apt install tesseract-ocr tesseract-ocr-spa  |  brew install tesseract tesseract-lang).
"""

from __future__ import annotations

import io
from pathlib import Path

from asistente.domain.models import Document

MIN_CHARS_PER_PAGE = 40  # por debajo de esto asumimos página escaneada → OCR
# Topes contra archivos hostiles: un PDF de 50 000 páginas o una imagen enorme pueden dejar
# al servidor trabajando indefinidamente. Pillow además rechaza imágenes con demasiados
# píxeles (DecompressionBombError) mientras no se cambie Image.MAX_IMAGE_PIXELS.
MAX_PAGES = 500
OCR_TIMEOUT_S = 120


def _ocr_image_bytes(data: bytes, lang: str = "spa") -> str:
    import pytesseract
    from PIL import Image

    with Image.open(io.BytesIO(data)) as image:
        return str(pytesseract.image_to_string(image, lang=lang, timeout=OCR_TIMEOUT_S))


def extract_text(path: Path, lang: str = "spa") -> str:
    suffix = path.suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}:
        return _ocr_image_bytes(path.read_bytes(), lang)
    if suffix == ".pdf":
        import pymupdf

        parts: list[str] = []
        with pymupdf.open(path) as pdf:  # type: ignore[no-untyped-call,unused-ignore]
            if pdf.page_count > MAX_PAGES:
                raise ValueError(f"El PDF tiene {pdf.page_count} páginas; máximo {MAX_PAGES}")
            for page in pdf:
                text = page.get_text()
                if len(text.strip()) < MIN_CHARS_PER_PAGE:
                    pix = page.get_pixmap(dpi=300)
                    text = _ocr_image_bytes(pix.tobytes("png"), lang)
                parts.append(text)
        return "\n\n".join(parts)
    return path.read_text(encoding="utf-8")


def load_document(path: Path) -> Document:
    return Document(
        title=path.stem,
        content=extract_text(path),
        source=str(path),
        metadata={"tipo": path.suffix.lstrip(".")},
    )
