#!/bin/bash
set -e

# Extract version from pyproject.toml
VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
echo "Starting Stocky Backend v${VERSION}..."

# Ensure data directory exists
mkdir -p /app/data

# Activate virtual environment
export VIRTUAL_ENV=/app/.venv
export PATH="$VIRTUAL_ENV/bin:$PATH"

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

echo "Starting application..."
exec uvicorn stocky_backend.main:app --host 0.0.0.0 --port 8000
