# Stocky Backend Testing Makefile
# 
# This Makefile provides convenient commands for running tests and development tasks.

.PHONY: help test test-unit test-integration test-api test-e2e test-all test-cov test-watch clean lint format setup install-test-deps docker-image

# Default target
help:
	@echo "Stocky Backend Testing Commands"
	@echo "==============================="
	@echo ""
	@echo "Setup Commands:"
	@echo "  setup                Install project and test dependencies"
	@echo "  install-test-deps    Install only test dependencies"
	@echo ""
	@echo "Testing Commands:"
	@echo "  test                 Run all tests"
	@echo "  test-unit           Run unit tests only"
	@echo "  test-integration    Run integration tests only"
	@echo "  test-api            Run API tests only"
	@echo "  test-e2e            Run end-to-end tests only"
	@echo "  test-cov            Run all tests with coverage report"
	@echo "  test-watch          Run tests in watch mode"
	@echo "  test-parallel       Run tests in parallel"
	@echo ""
	@echo "Quality Commands:"
	@echo "  lint                Run linting checks"
	@echo "  format              Format code with black and isort"
	@echo "  type-check          Run type checking with mypy"
	@echo "  security-scan       Run security scans"
	@echo ""
	@echo "Development Commands:"
	@echo "  clean               Clean test artifacts and cache"
	@echo "  requirements        Generate requirements.txt files"
	@echo ""
	@echo "Docker Commands:"
	@echo "  docker-image        Build production Docker image"
	@echo "  docker-test         Run tests in Docker container"
	@echo "  docker-build-test   Build test Docker image"

# Setup commands
setup: install-test-deps
	pip install -e .

install-test-deps:
	pip install -r tests/requirements-test.txt

# Core testing commands
test:
	pytest

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

test-api:
	pytest tests/api/ -v

test-e2e:
	pytest tests/e2e/ -v

test-all: test-unit test-integration test-api test-e2e

# Coverage testing
test-cov:
	pytest --cov=src/stocky_backend --cov-report=html --cov-report=term-missing --cov-report=xml

test-cov-unit:
	pytest tests/unit/ --cov=src/stocky_backend --cov-report=html --cov-report=term-missing

test-cov-integration:
	pytest tests/integration/ --cov=src/stocky_backend --cov-report=html --cov-report=term-missing

test-cov-api:
	pytest tests/api/ --cov=src/stocky_backend --cov-report=html --cov-report=term-missing

test-cov-e2e:
	pytest tests/e2e/ --cov=src/stocky_backend --cov-report=html --cov-report=term-missing

# Development testing
test-watch:
	pytest --looponfail

test-failed:
	pytest --lf

test-failed-first:
	pytest --ff

test-parallel:
	pytest -n auto

test-verbose:
	pytest -v -s

test-debug:
	pytest --pdb

# Specific test categories
test-auth:
	pytest -m auth -v

test-database:
	pytest -m database -v

test-slow:
	pytest -m slow -v

test-security:
	pytest -m security -v

test-external:
	pytest -m external -v

# Quality assurance commands
lint:
	flake8 src/ tests/
	pylint src/ tests/ || true

format:
	black src/ tests/
	isort src/ tests/

format-check:
	black --check src/ tests/
	isort --check src/ tests/

type-check:
	mypy src/ --ignore-missing-imports

security-scan:
	safety check
	bandit -r src/

# Performance testing
test-performance:
	pytest tests/ -m "slow" --benchmark-only

test-load:
	# Requires locust to be installed
	# locust -f tests/performance/locustfile.py --headless -u 10 -r 2 -t 30s

# Cleanup commands
clean:
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

clean-all: clean
	rm -rf .mypy_cache/
	rm -rf .tox/
	rm -rf *.egg-info/

# Requirements management
requirements:
	pip-compile pyproject.toml
	pip-compile tests/requirements-test.in

requirements-upgrade:
	pip-compile --upgrade pyproject.toml
	pip-compile --upgrade tests/requirements-test.in

# Docker testing commands
docker-image:
	docker buildx build --platform linux/amd64,linux/arm64 -t docker-registry.eruditio.net/stocky-backend:latest --push .

docker-build-test:
	docker build -t stocky-backend:test .

docker-test: docker-build-test
	docker run --rm \
		-v $(PWD):/app \
		-w /app \
		stocky-backend:test \
		pytest

docker-test-shell: docker-build-test
	docker run --rm -it \
		-v $(PWD):/app \
		-w /app \
		stocky-backend:test \
		/bin/bash

# Database testing commands
test-with-postgres:
	@echo "Starting PostgreSQL container for testing..."
	docker run --name postgres-test -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=stocky_test -p 5433:5432 -d postgres:15
	@echo "Waiting for PostgreSQL to be ready..."
	sleep 5
	DATABASE_URL=postgresql://postgres:postgres@localhost:5433/stocky_test pytest
	@echo "Stopping and removing PostgreSQL container..."
	docker stop postgres-test
	docker rm postgres-test

# CI/CD simulation
ci-test: clean lint type-check security-scan test-cov
	@echo "All CI checks passed!"

# Development workflow
dev-test: format lint test-unit test-integration
	@echo "Development tests completed!"

# Pre-commit checks
pre-commit: format-check lint type-check test-unit
	@echo "Pre-commit checks passed!"

# Install pre-commit hooks
install-hooks:
	pre-commit install

# Database migrations testing
test-migrations:
	pytest tests/integration/test_migrations.py -v

# Generate test data
generate-test-data:
	python scripts/generate_test_data.py

# Test specific files
test-file:
	@read -p "Enter test file path: " file; \
	pytest $$file -v

# Test specific function
test-function:
	@read -p "Enter test function name: " func; \
	pytest -k $$func -v

# Benchmark tests
benchmark:
	pytest tests/ --benchmark-only --benchmark-sort=mean

# Memory profiling
test-memory:
	pytest tests/ --memray

# Test with different Python versions (requires pyenv or similar)
test-python-versions:
	@for version in 3.11 3.12 3.13; do \
		echo "Testing with Python $$version"; \
		python$$version -m pytest tests/ || echo "Python $$version failed"; \
	done

# Documentation testing
test-docs:
	pytest --doctest-modules src/

# Report generation
report:
	pytest --html=report.html --self-contained-html

# Coverage report opening
open-coverage:
	@if [ -f htmlcov/index.html ]; then \
		open htmlcov/index.html; \
	else \
		echo "Coverage report not found. Run 'make test-cov' first."; \
	fi

# Test environment info
test-env:
	@echo "Python version: $$(python --version)"
	@echo "Pytest version: $$(pytest --version)"
	@echo "Test environment: $$(python -c 'import sys; print(sys.executable)')"
	@echo "Installed packages:"
	@pip list | grep -E "(pytest|coverage|factory|httpx)"
