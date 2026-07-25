# Stage 1: builder - instala dependências Python do projeto
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

RUN apt-get update && \
  apt-get install -y --no-install-recommends \
  build-essential \
  libpq-dev && \
  rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-install-project --no-dev --no-build


FROM python:3.12-slim AS base

WORKDIR /app

RUN apt-get update && \
  apt-get install -y --no-install-recommends \
  fonts-dejavu-core \
  libcairo2 \
  libgdk-pixbuf-2.0-0 \
  libglib2.0-0 \
  libgobject-2.0-0 \
  libharfbuzz0b \
  libpango-1.0-0 \
  libpangoft2-1.0-0 \
  libpq5 \
  netcat-traditional \
  shared-mime-info && \
  rm -rf /var/lib/apt/lists/*


COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY src ./src
COPY migrations ./migrations
COPY alembic.ini ./

RUN groupadd -r appuser \
  && useradd -r -g appuser -d /app -s /sbin/nologin appuser \
  && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]