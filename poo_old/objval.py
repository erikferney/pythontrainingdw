# objeto de valor y entidad
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Self
from uuid import uuid4


def ahora() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class Mensaje:
    rol: str
    contenido: str
    creado_en: datetime = field(
        default_factory=ahora, compare=False
    )  # default_factory para poder crear el mensaje sin tener que pasarlo como argumento
    # field para poder crear el campo creado_en
    # compare=False para que no se compare el campo creado_en


# entidad documento no inmutable
@dataclass(frozen=True)
class Documento:
    titulo: str
    contenido: str
    fuente: str = "manual"
    id: field(default_factory=uuid4, compare=False)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Documento) and self.id == other.id

    def __hash__(self):
        return hash(self.id)

    @classmethod
    def desde_archivo(cls, archivo: Path) -> Self:
        """Crear un documento desde un archivo"""
        if not archivo.is_file():
            raise FileNotFoundError(f"El archivo {archivo} no existe")
        if archivo.suffix.lower() not in (".txt", ".md"):
            raise ValueError(f"El archivo {archivo} no es un archivo de texto o markdown")

        contenido = archivo.read_text(encoding="utf-8")
        return cls(id=uuid4(), titulo=archivo.stem, contenido=contenido, fuente=str(archivo))


@dataclass(frozen=True)
class Fragmento:
    texto: str
    posicion: int
    embedding: list[float] | None = None

    # agregar un __post_init__ para que se ejecute después de la inicialización
    # valueerror si el embedding es None
    # valueerror si la posicion es negativa
    # valueerror si el texto es vacío
    # valueerror si texto es solo espacios
    def __post_init__(self):
        if self.embedding is None:
            raise ValueError("El embedding no puede ser NONE")
        if self.posicion < 0:
            raise ValueError("La posición no puede ser negativa")
        if not self.texto.strip():  # strip() para eliminar los espacios al inicio y al final
            raise ValueError("El texto no puede ser vacío")

    # agregar dos propiedades (@property) que se leen sin parentesis
    # vectorizado -> True si el embedding no es None
    # palabras -> cuantas palabras tiene el texto
    @property
    def vectorizado(self) -> bool:
        return self.embedding is not None

    @property
    def palabras(self) -> int:
        return len(self.texto.split())


@dataclass(frozen=True)
class Conversacion:
    _mensajes: list[Mensaje] = field(default_factory=list, compare=False)

    def agregar(self, rol: str, contenido: str) -> Mensaje:
        """Agregar un mensaje a la conversación"""
        mensaje = Mensaje(rol, contenido)
        self._mensajes.append(mensaje)
        return mensaje

    def __iter__(self) -> Iterator[Mensaje]:
        """Iterar sobre los mensajes de la conversación"""
        return iter(self._mensajes)

    def __len__(self) -> int:
        return len(self._mensajes)

    def __contains__(self, mensaje: Mensaje) -> bool:
        return mensaje in self._mensajes

    def __bool__(self) -> bool:
        return bool(self._mensajes)

    def __getitem__(self, index: int) -> Mensaje:
        return self._mensajes[index]

    @property
    def mensajes(self) -> tuple[Mensaje, ...]:
        """Obtener los mensajes de la conversación como una tupla para que no se pueda modificar"""
        return tuple(self._mensajes)
