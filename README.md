# Stocky Backend

A modern inventory management system backend built with FastAPI, SQLAlchemy, and Docker.

## Features

- **RESTful API** - Built with FastAPI for high performance and automatic documentation
- **Database Management** - SQLAlchemy ORM with SQLite (development) and PostgreSQL support
- **Authentication** - JWT-based authentication system
- **Docker Ready** - Fully containerized for easy deployment
- **API Documentation** - Automatic OpenAPI/Swagger documentation
- **Data Validation** - Pydantic models for robust data validation
- **CORS Support** - Configurable CORS for frontend integration

## Quick Start with Docker 🐳

The fastest way to get Stocky Backend running:

```bash
# Clone the repository
git clone <repository-url>
cd stocky-backend

# Start with Docker Compose
docker-compose up -d

# Verify it's running
curl http://localhost:8000/api/v1/health
```

The API will be available at `http://localhost:8000`

## Development Setup

### Prerequisites

- Python 3.11+
- pip or poetry
- SQLite (included with Python)

### Local Development

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd stocky-backend
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -e .
   ```

4. **Initialize database**:
   ```bash
   alembic upgrade head
   ```

5. **Run the development server**:
   ```bash
   uvicorn stocky_backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

The API will be available at `http://localhost:8000` with automatic reload on code changes.

## API Documentation

Once the server is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=sqlite:///./data/stocky.db

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]

# Application
DEBUG=false
CREATE_INITIAL_DATA=true
```

### Docker Configuration

For Docker deployment, environment variables are configured in `docker-compose.yml`. See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/refresh` - Refresh access token

### Users
- `GET /api/v1/users/me` - Get current user profile
- `PUT /api/v1/users/me` - Update user profile

### Items
- `GET /api/v1/items/` - List all items
- `POST /api/v1/items/` - Create new item
- `GET /api/v1/items/{id}` - Get item by ID
- `PUT /api/v1/items/{id}` - Update item
- `DELETE /api/v1/items/{id}` - Delete item

### Locations
- `GET /api/v1/locations/` - List all locations
- `POST /api/v1/locations/` - Create new location
- `GET /api/v1/locations/{id}` - Get location by ID
- `PUT /api/v1/locations/{id}` - Update location
- `DELETE /api/v1/locations/{id}` - Delete location

### SKUs
- `GET /api/v1/skus/` - List all SKUs
- `POST /api/v1/skus/` - Create new SKU
- `GET /api/v1/skus/{id}` - Get SKU by ID
- `PUT /api/v1/skus/{id}` - Update SKU
- `DELETE /api/v1/skus/{id}` - Delete SKU

### Scanner
- `POST /api/v1/scanner/scan` - Process barcode scan
- `GET /api/v1/scanner/history` - Get scan history

### Alerts
- `GET /api/v1/alerts/` - List all alerts
- `POST /api/v1/alerts/` - Create new alert
- `PUT /api/v1/alerts/{id}/acknowledge` - Acknowledge alert

### System
- `GET /api/v1/health` - Health check endpoint
- `GET /api/v1/logs/` - Get system logs

## Testing 🧪

Stocky Backend has comprehensive test coverage including unit, integration, API, and end-to-end tests.

### Quick Test Run

```bash
# Run all tests
make test

# Run specific test categories
make test-unit           # Unit tests only
make test-integration    # Integration tests only
make test-api           # API tests only
make test-e2e           # End-to-end tests only

# Run with coverage
make test-cov
```

### Test Structure

```
tests/
├── unit/                # Unit tests (isolated components)
├── integration/         # Integration tests (database + business logic)
├── api/                # API endpoint tests
├── e2e/                # End-to-end workflow tests
├── factories/          # Test data factories
├── fixtures/           # Reusable test fixtures
└── utils/              # Test utilities and helpers
```

### Test Features

- **Comprehensive Coverage**: 90%+ code coverage target
- **Fast Execution**: Optimized for quick feedback during development
- **Parallel Testing**: Tests run in parallel for faster execution
- **Database Isolation**: Each test uses clean database state
- **Factory Pattern**: Consistent test data generation
- **CI/CD Integration**: Automated testing on push/PR

### Running Tests

```bash
# Install test dependencies
pip install -r tests/requirements-test.txt

# Run specific test files
pytest tests/unit/test_auth.py -v

# Run tests with markers
pytest -m "unit" -v              # Unit tests only
pytest -m "auth" -v              # Authentication tests only
pytest -m "database" -v          # Database tests only

# Watch mode for development
pytest --looponfail

# Debug mode
pytest --pdb

# Performance testing
pytest -m "slow" --benchmark-only
```

### Test Configuration

- **pytest.ini**: Main test configuration
- **conftest.py**: Shared fixtures and test setup
- **Coverage**: HTML and XML coverage reports
- **CI/CD**: GitHub Actions workflow with multiple Python versions

For detailed testing information, see [TESTING.md](TESTING.md).

## Development

### Database Migrations

Using Alembic for database migrations:

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback to previous migration
alembic downgrade -1
```

### Running Tests (Legacy - see Testing section above)

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest

# Run tests with coverage
pytest --cov=stocky_backend
```

### Code Quality

```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

## Deployment

### Production Deployment

For production deployment, see [DEPLOYMENT.md](DEPLOYMENT.md) for comprehensive instructions including:

- Docker deployment
- Kubernetes configuration
- SSL/TLS setup
- Monitoring and logging
- Backup strategies
- Security considerations

### Quick Production Start

```bash
# Production deployment with Docker
docker-compose -f docker-compose.prod.yml up -d
```

## Architecture

### Project Structure

```
stocky-backend/
├── src/stocky_backend/          # Main application package
│   ├── api/                     # API routes and endpoints
│   ├── core/                    # Core configuration and security
│   ├── crud/                    # Database operations
│   ├── db/                      # Database configuration
│   ├── models/                  # SQLAlchemy models
│   ├── schemas/                 # Pydantic schemas
│   └── services/                # Business logic services
├── alembic/                     # Database migrations
├── scripts/                     # Utility scripts
├── docs/                        # Documentation
├── tests/                       # Test suites
├── Dockerfile                   # Docker configuration
├── docker-compose.yml           # Docker Compose configuration
└── pyproject.toml              # Project dependencies
```

### Technology Stack

- **Framework**: FastAPI
- **ORM**: SQLAlchemy 2.0
- **Database**: SQLite (dev), PostgreSQL (prod)
- **Authentication**: JWT with python-jose
- **Validation**: Pydantic v2
- **Migration**: Alembic
- **ASGI Server**: Uvicorn
- **Containerization**: Docker

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Write tests for new functionality
- Update documentation for API changes
- Use type hints throughout the codebase
- Keep commits atomic and well-described

## Troubleshooting

### Common Issues

1. **Database connection errors**:
   - Check DATABASE_URL in environment
   - Ensure database file permissions are correct
   - Run `alembic upgrade head` to apply migrations

2. **Import errors**:
   - Install package in development mode: `pip install -e .`
   - Check Python path and virtual environment

3. **Docker issues**:
   - Ensure Docker is running
   - Check port 8000 is not in use
   - Verify docker-compose.yml configuration

### Getting Help

- Check the [DEPLOYMENT.md](DEPLOYMENT.md) for deployment issues
- Review application logs: `docker-compose logs backend`
- Verify environment configuration
- Check API documentation at `/docs`

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Changelog

See [CHANGELOG.md](./CHANGELOG.md) for detailed version history and release notes.

## Contact

For questions and support, please open an issue in the repository.
