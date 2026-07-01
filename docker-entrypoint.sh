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

# Run database migrations (idempotent)
echo "Running database migrations..."

# Detect database state: fresh (no tables), existing without alembic history,
# or normal (has alembic_version table)
DB_STATE=$(python -c "
from sqlalchemy import create_engine, inspect, text
from stocky_backend.core.config import settings
url = settings.DATABASE_URL
if 'pysqlite' in url:
    url = url.replace('sqlite+pysqlite', 'sqlite')
engine = create_engine(url)
inspector = inspect(engine)
tables = inspector.get_table_names()
if not tables:
    print('FRESH')
elif 'alembic_version' not in tables:
    print('STAMP_NEEDED')
else:
    # alembic_version exists — check if it has a revision
    with engine.connect() as conn:
        row = conn.execute(text('SELECT version_num FROM alembic_version LIMIT 1')).first()
    if row and row[0]:
        print('UPGRADE')
    else:
        print('STAMP_NEEDED')  # table exists but empty
" 2>/dev/null || echo "FALLBACK")

case "$DB_STATE" in
    STAMP_NEEDED)
        echo "Existing database detected (no migration history). Stamping head..."
        alembic stamp head
        alembic upgrade head
        ;;
    FRESH)
        echo "Fresh database. Running full migration..."
        alembic upgrade head
        ;;
    UPGRADE)
        echo "Running pending migrations..."
        alembic upgrade head
        ;;
    *)
        echo "Could not determine DB state. Attempting upgrade with fallback..."
        alembic upgrade head || (alembic stamp head && alembic upgrade head)
        ;;
esac

echo "Starting application..."
exec uvicorn stocky_backend.main:app --host 0.0.0.0 --port 8000
