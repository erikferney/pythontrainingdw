x = 10  # no se declara: se asigna el valor
x = "diez"  # el nombre puede apuntar a otro tipo de dato
type(x)  # -> <class 'str'>
edad: int = 10  # se declara el tipo de dato, no obliga
edad = "diez"  # se puede cambiar el tipo de dato
a = [1, 2, 3]  # se puede asignar una lista
b = a  # no copia la lista, sino que apunta a la misma lista
b.append(4)
a  # se modifica la lista, y por lo tanto la lista a también
(
    a is b,
    a == [1, 2, 3],
)  # is es para ver si son el mismo objeto, == es para ver si tienen el mismo valor (True, True)
# (True, True) es una tupla y no se puede modificar

n = None  # n es None, no es 0 ni False ni '' ni [] ni {}
n is None  # True, para poder comparar con None se usa is
Total = 1
total = 2
Total == total  # True, Total y total son el mismo objeto

# COMO SE NOMBRAN LAS COSAS PEP8

# snake_case              #para variables, funciones, métodos, etc.
# CamelCase               #para clases RagService, RagUser, etc.
# MAYUSCULAS              #para constantes: LIMITE, TOTAL, etc.
# _nombre                 #para variables privadas: _nombre, _nombre_privado, etc. En python se usa _ para indicar que es privado, pero no es realmente privado.
# __nombre__              #para variables especiales: __nombre__, __nombre__ especial, etc. En python se usa __ para indicar que es especial, pero no es realmente especial.
# kebab-case              #para archivos
# ruff                    #para verificar el código: ruff check .
# PascalCase              #para módulos

# TIPOS DE DATO

int  # para números enteros: 1, 2, 3, etc. NO TIENEN LIMITES DE TAMAÑO
float  # para números decimales: 1.0, 2.0, 3.0, etc. NO TIENEN LIMITES DE TAMAÑO
1_000_000  # para números grandes: 1_000_000, 1_000_000.0, etc. Es una convención para mejorar la legibilidad.
f"{2 + 2} resultados"  # para strings: f"{2 + 2} resultados" es una forma de interpolar variables en un string.
[
    1,
    "dos",
    3.0,
]  # para listas: [1, "dos", 3.0] es una lista de números enteros, strings y números decimales. Modificable.
(
    1,
    "dos",
    3.0,
)  # para tuplas: (1, "dos", 3.0) es una tupla de números enteros, strings y números decimales. No modificable.
# una tupla puede tener una lista, y esa lista si se puede modificar

{"clave": "valor"}  # diccionario: clave -> valor
"año"[0], "año"[-1], len("año")  # ('a', 'o', 3)

# OPERADORES

7 / 2, 7 // 2, 7 % 2, 2**3  # 3.5, 3, 1, 8
# / división y siempre retorna un valor decimal
# // división entera
# % el residuo de la división
# ** potencia

x = 5
0 < x <= 10  # True
x > 0 and x < 3, not x  # (False, False), cuando un valor entero no es cero, retorna False
"por defecto"  # el vacio es un False, retorna "por defecto"
"par" if x % 2 == 0 else "impar"  # impar, porque x = 5
x += 1
x  # 6
(n := len("hola")) > 3  # asigna la longitud a n, siempre y cuando la longitud sea mayor que 3


# bucles

docs = ["a.pdf", "b.pdf"]

for _doc in docs:  # se puede hacer cualquier cosa con la variable doc
    pass

for _i, _doc in enumerate(
    docs, start=1
):  # en i me queda la posición y en doc el valor, arranca en 1
    pass

for _clave, _valor in {
    "a": 1
}.items():  # recorre diccionarios, clave queda la clave, y valor el valor de la clave
    pass

[
    i for i in range(3)
]  # se crea una lista i, que va  tener los valores [0,1,2], range ocupa n - 1, 3 - 1 = 2


# funciones

# en una función puedo pasar los parámetros por indice o por nombre,
# por nombre del parámetro, podría ser la posición en cualquier lugar


def partir(texto: str, tamano: int = 3) -> list[str]:
    """Parte el texto en trozos de 'tamaño' caracteres."""
    return [texto[i : i + tamano] for i in range(0, len(texto), tamano)]


partir("abcdefg")  # ['abc', 'def', 'g']
partir("abddefg", 4)  # ['abcd', 'efg']
partir(
    tamano=2, texto="abcdefg"
)  # ['ab', 'cd', 'ef', 'g'], LLAMAR LAS FUNCIONES CON NOMBRES DE PARÁMETROS

# PARAMETROS ESPECIALES Y UNA TRAMPA

# *detalles: con el asterísco, va a crear una tupla con valores de parámetros sin nombre
# **campos: con 2 asteríscos, crea un diccionario con los parámetros con nombre valor


def registrar(evento, *detalles, nivel="info", **campos) -> str:
    return f"{nivel}: {evento} {detalles} {campos}"


registrar("login")  # 'info: login () {}'
registrar("x", "a", nivel="w", ms=1)  # "w: x ('a',) {'ms': 1}"


def malo(
    x, lista=None
):  # en este caso la lista se instancia una vez, cada llamado de función, lleva la misma referencia de la lista
    if lista is None:
        lista = []
    lista.append(x)
    return lista


malo(1), malo(2)


def agregar(lista: list[int]) -> None:  # modifica el objeto que recibió
    lista.append(99)


def reasignar(lista: list[int]) -> None:  # modifica lista pero como objeto local de la función
    pass


datos = [1]
agregar(datos)
datos  # [1, 99]
reasignar(datos)
datos  # [1, 99], no reasigna la lista,


# LAS FUNCIONES SE PUEDEN ASIGNAR A VARIABLES


def gritar(t: str) -> str:
    return t.upper()


f = gritar  # sin paréntesis, asigna la función a f
f("hola")  # retorna HOLA
list(
    map(gritar, ["a", "b"])
)  # map, hace que llame la función gritar, con cada uno de los items de la lista, y retorna una lista
sorted(["bb", "a", "ccc"], key=len)  # ["a", "bb", "ccc"]


def doble(x):
    return x * 2  # función anónima de una expresión


doble(4)  # 8


def fabrica(n: int):
    def sumar(x: int) -> int:
        return x + n  # closure

    return sumar


fabrica(10)(5)  # el primer parámetro es para fabrica, el segundo es para sumar
