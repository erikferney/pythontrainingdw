def clasificar(n: int) -> str:
    if n < 0:
        return "negativo"
    elif n == 0:
        return "cero"
    else:
        return "positivo"


def pendiente() -> None:
    pass  # no hace nada, solo para que el compilador no se queje


print(clasificar(1))
print(clasificar(0))
print(clasificar(-1))

total = 1 + 2 + 3 + 4 + 5  # se puede hacer una línea larga, pero se debe indentar

print(total)
