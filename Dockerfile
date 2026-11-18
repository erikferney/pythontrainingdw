# Sesión 7 / 13: imagen multi-etapa con uv
FROM python:3.12-slim AS build
# Versión fija, nunca "latest": la misma imagen hoy y en seis meses
COPY --from=ghcr.io/astral-sh/uv:0.12.22 /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY pyproject.toml uv.lock ./
# --locked: falla si uv.lock no corresponde a pyproject.toml
RUN uv sync --locked --no-dev --extra llm --no-install-project
COPY src ./src
RUN uv sync --locked --no-dev --extra llm

FROM python:3.12-slim
RUN useradd --create-home app
WORKDIR /app
# El código queda de root: el usuario app lo ejecuta, pero no puede modificarlo
COPY --from=build /app /app
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
USER app
EXPOSE 8000
HEALTHCHECK CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:8000/v1/health')"
CMD ["uvicorn", "asistente.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
