"""Práctica de la sesión 3, ejercicio 3: importar no debería hacer nada.

Diapositiva "Importar no debería hacer nada". Hoy, solo con importar este módulo se "conecta"
al proveedor. Arréglelo para que importar no llame a conectar() y la conexión ocurra dentro de
main(). Pruebe las dos formas:

    uv run pytest buenas_practicas -k arranque
    uv run python buenas_practicas/arranque.py         # debe imprimir: usando cliente-ollama
"""

from __future__ import annotations

LLAMADAS: list[str] = []


def conectar() -> str:
    """Simula conectarse a un proveedor de IA: es lento y necesita la llave."""
    LLAMADAS.append("conectar")
    return "cliente-ollama"


cliente = conectar()


def main() -> str:
    return f"usando {cliente}"


if __name__ == "__main__":
    print(main())
