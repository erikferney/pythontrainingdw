# data class inmutable
from dataclasses import dataclass


@dataclass(frozen=True)
class Cita:
    fuente: int
    extracto: str


cita1 = Cita(1, "Hola")
cita2 = Cita(1, "Hola")

print(cita1 == cita2)
print(cita1.fuente)
print(cita1.extracto)
