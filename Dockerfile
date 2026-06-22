# ---------- Estágio 1: build (instala dependências via Poetry) ----------
FROM python:3.13-slim AS builder

ENV POETRY_HOME="/opt/poetry" \
  POETRY_NO_INTERACTION=1 \
  POETRY_VIRTUALENVS_IN_PROJECT=1

RUN pip install --no-cache-dir poetry

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-root --only main --no-cache

# ---------- Estágio 2: imagem final (somente runtime) ----------
FROM python:3.13-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
  PYTHONPATH="/app/src" \
  PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY src ./src

EXPOSE 8000

CMD ["uvicorn", "photos_etl.api.app:app", "--host", "0.0.0.0", "--port", "8000"]