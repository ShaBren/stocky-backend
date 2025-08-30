# Use Python 3.13 slim image
FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

# Copy source code first
COPY ./src ./src
COPY ./alembic ./alembic
COPY ./alembic.ini ./alembic.ini
COPY ./scripts ./scripts
COPY ./docker-entrypoint.sh ./docker-entrypoint.sh
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Create necessary directories and fix permissions
RUN mkdir -p /app/data && chown -R appuser:appuser /app && chmod 755 /app/data

# Switch to non-root user
USER appuser

# Expose the port the app runs on
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["./docker-entrypoint.sh"]

