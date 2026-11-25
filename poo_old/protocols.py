from typing import Protocol, runtime_checkable


@runtime_checkable
class Buscador(Protocol):
    """se establece una firma de función"""

    def buscar(self, texto: str) -> list[str]: ...


class EnMemoria:
    """no hereda"""

    def buscar(self, texto: str) -> list[str]:
        return [d for d in self.docs if consulta in d]


def responder(buscador: Buscador, pregunta: str) -> str: ...
