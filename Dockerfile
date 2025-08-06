# Stage 1: Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install uv for dependency management
RUN pip install uv

# Copy dependency files and install dependencies
COPY pyproject.toml ./
RUN uv pip install --system --no-cache --no-deps -p pyproject.toml

# Copy the application source code
COPY ./src ./src


# Stage 2: Final production stage
FROM python:3.11-slim

WORKDIR /app

# Create a non-root user for security
RUN useradd --create-home appuser
USER appuser

# Copy installed dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the application source code
COPY --chown=appuser:appuser ./src ./src

# Create a volume for the SQLite database
VOLUME /app/data

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "stocky.main:app", "--host", "0.0.0.0", "--port", "8000"]

