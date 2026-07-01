# Stocky Backend — Development Commands
# All commands use `uv run` — no need to activate a virtual environment.

.PHONY: help test test-unit test-integration test-api test-e2e test-all test-cov lint format format-check type-check security-scan clean docker-image

help:
	@echo "Stocky Backend — Development Commands"
	@echo "======================================"
	@echo ""
	@echo "Setup:"
	@echo "  uv sync              Install all dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  make test            Run all tests"
	@echo "  make test-unit       Run unit tests only"
	@echo "  make test-integration Run integration tests only"
	@echo "  make test-api        Run API tests only"
	@echo "  make test-e2e        Run end-to-end tests only"
	@echo "  make test-all        Run all test categories"
	@echo "  make test-cov        Run all tests with coverage HTML report"
	@echo ""
	@echo "Quality:"
	@echo "  make lint            Lint with ruff"
	@echo "  make format          Format with ruff"
	@echo "  make format-check    Check formatting (CI)"
	@echo "  make type-check      Type check with mypy"
	@echo "  make security-scan   Security-focused lint with ruff"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-image    Build and push multi-arch Docker image"
	@echo "  make clean           Remove build artifacts and caches"

# ---- Testing ----

test:
	uv run pytest

test-unit:
	uv run pytest tests/unit/ -v

test-integration:
	uv run pytest tests/integration/ -v

test-api:
	uv run pytest tests/api/ -v

test-e2e:
	uv run pytest tests/e2e/ -v

test-all:
	uv run pytest tests/unit/ tests/integration/ tests/api/ tests/e2e/ -v

test-cov:
	uv run pytest --cov=src/stocky_backend --cov-report=html --cov-report=term-missing --cov-report=xml

# ---- Quality ----

lint:
	uv run ruff check .

format:
	uv run ruff format .

format-check:
	uv run ruff format --check .

type-check:
	uv run mypy src/

security-scan:
	uv run ruff check . --select=S

# ---- Docker ----

docker-image:
	docker buildx build --platform linux/amd64,linux/arm64 -t ghcr.io/shabren/stocky-backend:latest --push .

# ---- Cleanup ----

clean:
	rm -rf htmlcov/ .coverage coverage.xml .pytest_cache/ .mypy_cache/ .ruff_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
