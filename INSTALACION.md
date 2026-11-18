# Instalación

## Antes del lunes 23 de noviembre: Ollama en 5 pasos

Las tres últimas clases usan un modelo de IA que corre en su propio equipo, gratis y sin enviar
datos a nadie. Hágalo en casa: la descarga de los modelos tarda (de 3 a 10 GB) y en clase no hay
tiempo. Toma unos 30 minutos, casi todos esperando la descarga.

Si prefiere ir paso a paso, con lo que debe ver en cada comando y qué hacer si algo falla, use
el manual en PDF para Windows, macOS y Linux: [`Instalar-IA-del-curso.pdf`](Instalar-IA-del-curso.pdf).
Incluye también Tesseract, que se usa en la clase 3.

**1. Vea cuánta memoria tiene su equipo.**

| Sistema | Cómo verla |
|---|---|
| macOS | Menú Apple → Acerca de esta Mac → "Memoria" |
| Windows | `Ctrl+Shift+Esc` → Rendimiento → Memoria (el total, arriba a la derecha) |
| Linux | `free -h` → columna `total` de la fila `Mem` |

**2. Instale Ollama** y déjelo abierto.

- macOS: descargue la app de <https://ollama.com/download> (o `brew install --cask ollama`) y ábrala
  una vez: queda un ícono de llama en la barra de arriba.
- Windows: `winget install --id Ollama.Ollama` (o el instalador de <https://ollama.com/download>).
  Queda corriendo junto al reloj.
- Linux: `curl -fsSL https://ollama.com/install.sh | sh`.

Compruebe en una terminal nueva: `ollama --version`.

**3. Descargue dos modelos, según su memoria.** El de embeddings es el mismo para todos.

| Memoria | Comandos |
|---|---|
| 8 GB | `ollama pull qwen3:1.7b` y `ollama pull qwen3-embedding:0.6b` |
| 16 GB | `ollama pull qwen3:4b-instruct` y `ollama pull qwen3-embedding:0.6b` |
| 24 GB o más | `ollama pull qwen3:14b` y `ollama pull qwen3-embedding:0.6b` |

Pruebe el de chat: `ollama run qwen3:4b-instruct "Hola, responde en una frase"` (con el nombre del
suyo). Para salir de `ollama run`, `/bye`.

**4. Configure el proyecto.** En la raíz de su repositorio del curso, después de traer `s07-c1.2`:

```bash
uv sync --extra llm --extra docs   # instala los clientes de los modelos y de documentos
cp .env.example .env               # Windows (PowerShell): copy .env.example .env
```

Desde ahora, cada vez que sincronice, use `uv sync --extra llm --extra docs`: un `uv sync` solo
desinstala esos paquetes.

Abra `.env` y cambie solo dos líneas, con el modelo que descargó:

```bash
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen3:4b-instruct
```

**5. Verifique.**

```bash
uv run --env-file .env python scripts/verificar_ia.py
```

Debe terminar con `Todo listo para las clases de IA.` Si algo falla, el script dice qué hacer.
Mande una captura de esa salida al chat del curso.

| Si ve | Qué hacer |
|---|---|
| `✗ No responde en http://localhost:11434/v1` | Ollama no está abierto: ábralo (Linux: `ollama serve`) |
| `✗ Falta qwen3:…` | El `ollama pull` no terminó, o el nombre del `.env` no coincide con `ollama list` |
| `✗ OLLAMA_MODEL está vacío` | Faltó el `.env` o el `--env-file .env` |
| `✗ Falta el paquete openai` | `uv sync --extra llm --extra docs` |
| `ollama: command not found` | Cierre y vuelva a abrir la terminal; en Windows, reinicie la sesión |
| El chat tarda más de un minuto cada vez | El modelo es grande para su memoria: use el de la fila de arriba en la tabla del paso 3, y cierre el navegador y Docker mientras prueba |

¿Sin equipo para modelos locales? El curso funciona con `LLM_PROVIDER=fake`: todas las pruebas
pasan; solo no verá respuestas reales. Y quien tenga llave de un proveedor comercial puede usarla
(ver al final).

El resto de esta guía es la referencia completa, con lo que se usa en todo el curso.

---

El curso funciona completo **sin ningún modelo de IA**: el proyecto trae un proveedor falso
(`FakeLLM`) y embeddings que no necesitan red. Los modelos locales y las llaves comerciales se
usan para probar con IA de verdad, a partir de la sesión 6. Instale cada cosa antes de la sesión
en la que se usa.

| Para la sesión | Qué se necesita |
|---|---|
| 1 (5 oct) | Git, [uv](https://docs.astral.sh/uv/) y un editor (VS Code o PyCharm). Python no hace falta instalarlo aparte: `uv sync` descarga Python 3.12 si no lo tiene |
| 6 (26 oct) | Ollama y el modelo de su tamaño (ver tabla); conviene instalarlo antes de la sesión 5 |
| 7 (28 oct) | Docker |
| 8 (4 nov) | El segundo modelo de su tamaño, o una llave de un proveedor comercial |
| 10 (11 nov) | Modelo de embeddings: `ollama pull qwen3-embedding:0.6b` |
| 11 (18 nov) | Tesseract con el idioma español, y el modelo de visión de su tamaño |

## Una regla: Ollama va nativo, no dentro de Docker

Ollama usa la tarjeta gráfica para que los modelos respondan rápido. En Mac, Docker no tiene
acceso a la GPU, y en Windows y Linux solo con configuración adicional: un modelo dentro de un
contenedor correría con el procesador y sería muy lento. Por eso Ollama se instala como
aplicación normal, y lo que corre en Docker (la API del asistente) se conecta a él por
`http://host.docker.internal:11434/v1`.

## macOS

```bash
brew install uv git
brew install --cask ollama docker-desktop  # o la app OrbStack
brew install tesseract tesseract-lang      # OCR, con el paquete de idiomas
```

Abra la aplicación Ollama una vez para que quede corriendo.

## Windows

```powershell
winget install --id astral-sh.uv
winget install --id Git.Git
winget install --id Ollama.Ollama
winget install --id Docker.DockerDesktop     # requiere WSL 2
winget install --id UB-Mannheim.TesseractOCR
```

- Tesseract: en el instalador marque el idioma **Spanish**, y agregue la carpeta de instalación
  (por ejemplo `C:\Program Files\Tesseract-OCR`) a la variable `PATH`.
- Ollama usa la GPU NVIDIA automáticamente; sin GPU, funciona con el procesador, más lento.

## Linux (Ubuntu)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
curl -fsSL https://ollama.com/install.sh | sh
sudo apt install git docker.io tesseract-ocr tesseract-ocr-spa
```

En Linux, `host.docker.internal` no existe por defecto: al correr un contenedor que use Ollama,
agregue `--add-host=host.docker.internal:host-gateway` (en `docker-compose.yml`:
`extra_hosts: ["host.docker.internal:host-gateway"]`).

## Qué modelos descargar según la memoria de su equipo

| Memoria (RAM, o unificada en Mac) | Chat principal | Segundo modelo (sesión 8) | Visión (sesión 11) |
|---|---|---|---|
| 8 GB | `qwen3:1.7b` | `qwen3:0.6b` | Proveedor comercial, o solo Tesseract |
| 16 GB | `qwen3:4b-instruct` | `qwen3:1.7b` | `qwen2.5vl:3b` |
| 24 GB o más | `qwen3:14b` | `gpt-oss:20b` (cárguelo solo) | `qwen2.5vl:7b` |

Todos usan el mismo modelo de embeddings: `qwen3-embedding:0.6b`. En la sesión 8 se comparan dos
modelos; el segundo puede ser el de la tabla o un proveedor comercial. Con poca memoria, cierre
Docker y el navegador mientras prueba un modelo: el modelo, el sistema y sus programas comparten
la misma memoria, y conviene tener uno solo cargado a la vez.

Descárguelos con tiempo: suman de 3 a 30 GB según el equipo. Por ejemplo, con 16 GB:

```bash
ollama pull qwen3:4b-instruct        # chat principal, antes de la sesión 6
ollama pull qwen3:1.7b               # segundo modelo, antes de la sesión 8
ollama pull qwen3-embedding:0.6b     # embeddings, antes de la sesión 10
ollama pull qwen2.5vl:3b             # visión, antes de la sesión 11
ollama run qwen3:4b-instruct "Hola, responde en una frase"
```

En su `.env` (copia de `.env.example`), ponga el modelo principal que descargó:

```bash
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen3:4b-instruct
```

Los modelos Qwen3 y gpt-oss pueden "pensar" antes de responder, lo que multiplica el tiempo de
respuesta. El kit lo desactiva por defecto (`OLLAMA_REASONING=none` en `.env`). Por eso el modelo
de 16 GB es `qwen3:4b-instruct` y no `qwen3:4b`: este último siempre razona y tarda unas diez veces
más.

Y ejecute cargando ese archivo: `uv run --env-file .env uvicorn asistente.api.main:app --reload`.

## Sin equipo para modelos locales

- Siga con `LLM_PROVIDER=fake`: todos los talleres y pruebas funcionan.
- O use un proveedor comercial con su llave (`LLM_PROVIDER=openai` o `anthropic` en `.env`).
  Ponga un **límite de gasto** en el panel del proveedor y nunca suba el `.env` a Git.

## Dev Container y Codespaces

El repositorio trae un Dev Container (`.devcontainer/`) con Python, uv, Docker y Tesseract.
Ollama **no** va adentro: instálelo en su equipo como se explica arriba; el contenedor ya está
configurado para encontrarlo en `host.docker.internal`.

GitHub Codespaces corre en la nube y no puede ver el Ollama de su equipo: ahí use
`LLM_PROVIDER=fake` o un proveedor comercial.

## Verificar todo

```bash
uv --version
git --version
curl http://localhost:11434/v1/models     # lista los modelos de Ollama
tesseract --list-langs                    # debe incluir spa
docker run --rm hello-world               # desde la sesión 7
```
