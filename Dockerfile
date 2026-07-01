# syntax=docker/dockerfile:1
FROM python:3.13-slim AS build

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy source code
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./
COPY docker-entrypoint.sh ./

# Install the project itself
RUN uv sync --frozen --no-dev

# ---- Runtime stage ----
FROM python:3.13-slim

RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Copy virtual environment from build stage
COPY --from=build /app/.venv /app/.venv

# Copy application code
COPY --from=build /app/src /app/src
COPY --from=build /app/alembic /app/alembic
COPY --from=build /app/alembic.ini /app/alembic.ini
COPY --from=build /app/docker-entrypoint.sh /app/docker-entrypoint.sh

# Create data directory
RUN mkdir -p /app/data && chown -R appuser:appuser /app && chmod 755 /app/data

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

ENTRYPOINT ["./docker-entrypoint.sh"]
