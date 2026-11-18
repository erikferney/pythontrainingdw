"""Sesión 11 (código seguro): validar un archivo subido antes de procesarlo.

Tamaño con tope al leer, tipo por el contenido (no por el nombre) y nombre propio en disco.
"""

from __future__ import annotations

MAX_BYTES = 20 * 1024 * 1024
FIRMAS = {
    b"%PDF-": ".pdf",
    b"\x89PNG\r\n\x1a\n": ".png",
    b"\xff\xd8\xff": ".jpg",
}


# taller: s11
def detectar_tipo(datos: bytes, nombre: str) -> str:
    """Extensión segura para guardar el archivo, decidida por sus primeros bytes.

    El texto plano no tiene firma: se acepta un .txt o .md solo si es UTF-8 válido.
    Lanza FileTooLargeError o UnsupportedFormatError.
    """
    raise NotImplementedError
