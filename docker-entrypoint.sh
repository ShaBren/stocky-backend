#!/bin/bash
set -e

# Extract version from pyproject.toml
VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
echo "Starting Stocky Backend v${VERSION}..."

# Ensure data directory exists
mkdir -p /app/data

# Initialize database if it doesn't exist
if [ ! -f "/app/data/stocky.db" ]; then
    echo "Creating new database file..."
    touch /app/data/stocky.db
fi

echo "Starting application..."
exec uvicorn stocky_backend.main:app --host 0.0.0.0 --port 8000
