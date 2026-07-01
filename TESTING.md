# Stocky Backend — Testing Guide

## Quick Start

```bash
uv sync --group dev --group postgres
make test
```

## Test Categories

| Command | Scope |
|---|---|
| `make test` | All tests |
| `make test-unit` | Unit tests only (`tests/unit/`) |
| `make test-integration` | Integration tests only (`tests/integration/`) |
| `make test-api` | API endpoint tests (`tests/api/`) |
| `make test-e2e` | End-to-end workflow tests (`tests/e2e/`) |
| `make test-cov` | All tests with HTML coverage report |

## Toolchain

All quality checks use `uv run` — no need to activate a virtual environment:

| Command | Tool | Description |
|---|---|---|
| `make lint` | ruff | Fast Python linter (pycodestyle + pyflakes) |
| `make format` | ruff | Code formatter |
| `make format-check` | ruff | Check formatting (used in CI) |
| `make type-check` | mypy | Static type checking |
| `make security-scan` | ruff (S rules) | Security-focused lint (excludes tests/scripts/alembic) |

## Configuration

Test configuration lives in `pyproject.toml` under `[tool.pytest.ini_options]`:

- **Test paths**: `tests/`
- **Marks**: `unit`, `integration`, `api`, `e2e`, `slow`, `auth`, `database`, `external`, `security`
- **Async mode**: `auto`
- **Coverage**: Enabled by default (HTML, XML, term-missing)

## CI

GitHub Actions runs the full pipeline on push/PR to `main` and `develop`:
1. Lint + format check (ruff)
2. Type check (mypy)
3. Security scan (ruff S rules, production code only)
4. Test suite on PostgreSQL (Python 3.11, 3.12, 3.13)

## Test Structure

```
tests/
├── conftest.py          # Shared fixtures and configuration
├── unit/                # Isolated component tests
├── integration/         # Database integration tests
├── api/                 # HTTP endpoint tests
├── e2e/                 # Complete workflow tests
├── factories/           # Test data factories (factory-boy)
└── utils/               # Test helpers
```

## Writing Tests

### Unit Test Example

```python
def test_password_hashing():
    hashed = hash_password("testpass123")
    assert hashed != "testpass123"
    assert verify_password("testpass123", hashed) is True
```

### API Test Example

```python
@pytest.mark.asyncio
async def test_create_item(async_client, auth_headers_admin):
    response = await async_client.post(
        "/api/v1/items/",
        json={"name": "Test Item", "upc": "123456789012"},
        headers=auth_headers_admin,
    )
    assert response.status_code == 201
```

### Database Test Example

```python
def test_create_user(db_session):
    user = User(username="test", email="test@test.com", hashed_password="hash")
    db_session.add(user)
    db_session.commit()
    assert user.id is not None
```
