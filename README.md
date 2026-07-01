# Stocky Backend

A modern home kitchen inventory management system backend built with FastAPI, SQLAlchemy, and uv.

## Features

- **RESTful API** — FastAPI with automatic OpenAPI documentation
- **Barcode Scanner Support** — UPC lookup, stub item creation, background product data enrichment
- **Inventory Management** — Items, locations, SKUs with quantities and expiries
- **Shopping Lists** — Collaborative lists with audit logging
- **Authentication** — JWT + API key auth with role-based access (admin, member, scanner, read-only)
- **PostgreSQL + SQLite** — SQLite for dev, PostgreSQL for production
- **Docker Ready** — Multi-arch image (amd64/arm64) with GHCR releases
- **uv Toolchain** — Fast dependency management, linting, and testing via uv

## Quick Start

```bash
git clone https://github.com/ShaBren/stocky-backend.git
cd stocky-backend

# Install uv if needed: curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Run lints, type checks, and tests
make lint && make type-check && make test

# Start the server
uv run uvicorn stocky_backend.main:app --reload
```

The API will be available at `http://localhost:8000`. Docs at `http://localhost:8000/docs` (with `DEBUG=true`).

## Docker

```bash
docker compose up -d
curl http://localhost:8000/api/v1/health
```

Multi-arch images published to `ghcr.io/shabren/stocky-backend` on every tagged release.

## Development Commands

| Command | Description |
|---|---|
| `make test` | Run all tests |
| `make lint` | Lint with ruff |
| `make format` | Format with ruff |
| `make type-check` | Type check with mypy |
| `make test-cov` | Tests with coverage HTML report |
| `make docker-image` | Build and push multi-arch Docker image |

## Configuration

All settings via environment variables or `.env` file. See [DEPLOYMENT.md](DEPLOYMENT.md) for the full list.

Key settings:
- `DATABASE_URL` — defaults to SQLite, set to PostgreSQL for production
- `SECRET_KEY` — JWT signing key (**required** in production)
- `UPC_SERVICE_BASE_URL` — optional external UPC lookup service (e.g. `http://10.0.0.200:8242`)

## Documentation

- [API Reference](docs/api-reference.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Testing Guide](TESTING.md)
- [Changelog](CHANGELOG.md)
- [System Design](docs/system-design.md)

## License

MIT — see [LICENSE](LICENSE).
