"""Cuenta las palabras de un texto. Esto es un docstring del módulo."""

from collections import Counter  # importar lo que se usa

LIMITE = 3  # definir una constante SIEMPRE EN MAYUSCULAS


def contar(texto: str) -> list[tuple[str, int]]:
    """Las palabras más frecuentes."""
    palabras = texto.lower().split()
    return Counter(palabras).most_common(LIMITE)


def main() -> None:
    """Función principal."""
    texto = "el sol y el mar y el cielo"
    print(contar(texto))


if __name__ == "__main__":  # solo al ejercutarlo directamente
    main()
