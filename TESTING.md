# Stocky Backend Testing Framework Design

## Overview

This document outlines the comprehensive testing strategy for the Stocky Backend API. The testing framework is designed to be thorough, maintainable, and easily extensible while ensuring high code coverage and reliability.

## Testing Philosophy

Our testing approach follows the **Test Pyramid** principle:
- **Unit Tests (70%)**: Fast, isolated tests for individual components
- **Integration Tests (20%)**: Tests for component interactions and database operations
- **End-to-End Tests (10%)**: Full API workflow tests

## Testing Stack

### Core Testing Dependencies
- **pytest**: Main testing framework with powerful fixtures and parametrization
- **pytest-asyncio**: Async/await support for FastAPI testing
- **pytest-cov**: Code coverage reporting
- **httpx**: HTTP client for API testing
- **factory-boy**: Test data factories for consistent test data generation
- **freezegun**: Time manipulation for time-dependent tests
- **pytest-mock**: Enhanced mocking capabilities

### Database Testing
- **SQLAlchemy**: In-memory SQLite for fast test execution
- **pytest-xdist**: Parallel test execution
- **alembic**: Database migration testing

## Project Structure

```
tests/
├── conftest.py                 # Shared pytest configuration and fixtures
├── pytest.ini                  # Pytest configuration
├── requirements-test.txt        # Test-specific dependencies
├── 
├── unit/                       # Unit tests (isolated component testing)
│   ├── __init__.py
│   ├── test_auth.py            # Authentication logic tests
│   ├── test_crud.py            # CRUD operations tests
│   ├── test_models.py          # SQLAlchemy model tests
│   ├── test_schemas.py         # Pydantic schema validation tests
│   ├── test_security.py        # Security utilities tests
│   └── test_config.py          # Configuration tests
│
├── integration/                # Integration tests (database + business logic)
│   ├── __init__.py
│   ├── test_database.py        # Database integration tests
│   ├── test_migrations.py      # Alembic migration tests
│   ├── test_services.py        # Business logic integration tests
│   └── test_external_apis.py   # External service integration tests
│
├── api/                        # API endpoint tests (full request/response cycle)
│   ├── __init__.py
│   ├── test_auth_api.py        # Authentication endpoint tests
│   ├── test_users_api.py       # User management API tests
│   ├── test_items_api.py       # Item management API tests
│   ├── test_locations_api.py   # Location management API tests
│   ├── test_skus_api.py        # SKU/inventory API tests
│   ├── test_scanner_api.py     # Scanner interaction API tests
│   ├── test_alerts_api.py      # Alert management API tests
│   ├── test_logs_api.py        # Logging API tests
│   └── test_health_api.py      # Health check API tests
│
├── e2e/                        # End-to-end workflow tests
│   ├── __init__.py
│   ├── test_user_workflows.py  # Complete user workflows
│   ├── test_inventory_workflows.py # Inventory management workflows
│   └── test_scanner_workflows.py   # Scanner-based workflows
│
├── factories/                  # Test data factories
│   ├── __init__.py
│   ├── user_factory.py         # User test data factory
│   ├── item_factory.py         # Item test data factory
│   ├── location_factory.py     # Location test data factory
│   ├── sku_factory.py          # SKU test data factory
│   └── alert_factory.py        # Alert test data factory
│
├── fixtures/                   # Reusable test fixtures
│   ├── __init__.py
│   ├── auth_fixtures.py        # Authentication-related fixtures
│   ├── database_fixtures.py    # Database setup/teardown fixtures
│   └── api_fixtures.py         # API client fixtures
│
└── utils/                      # Test utilities and helpers
    ├── __init__.py
    ├── test_helpers.py         # Common test helper functions
    ├── assertions.py           # Custom assertion helpers
    └── mock_data.py            # Mock data generators
```

## Testing Categories

### 1. Unit Tests

**Purpose**: Test individual components in isolation
**Scope**: Single functions, classes, or modules
**Database**: No database interaction (mocked)

**Coverage Areas**:
- **Authentication Logic**: Password hashing, JWT generation/validation
- **CRUD Operations**: Database query logic (mocked database)
- **Pydantic Schemas**: Data validation and serialization
- **Business Logic**: Core application logic
- **Utility Functions**: Helper functions and utilities

**Example Test Structure**:
```python
class TestUserCRUD:
    def test_create_user_with_valid_data(self, mock_db):
        # Test user creation with valid input
        
    def test_create_user_with_invalid_data(self, mock_db):
        # Test validation errors
        
    def test_get_user_by_id(self, mock_db):
        # Test user retrieval
```

### 2. Integration Tests

**Purpose**: Test component interactions and database operations
**Scope**: Multiple components working together
**Database**: Real database with transactions (rolled back after each test)

**Coverage Areas**:
- **Database Operations**: Real CRUD operations with SQLAlchemy
- **Migration Testing**: Alembic migration validation
- **Service Layer Integration**: Business logic with database
- **Authentication Flows**: Complete auth workflows

**Example Test Structure**:
```python
class TestUserService:
    def test_create_user_end_to_end(self, db_session):
        # Test complete user creation flow with database
        
    def test_user_authentication_flow(self, db_session):
        # Test login/token generation with real database
```

### 3. API Tests

**Purpose**: Test HTTP API endpoints
**Scope**: Full request/response cycle
**Database**: Test database with proper isolation

**Coverage Areas**:
- **All API Endpoints**: Every route in the application
- **Authentication & Authorization**: JWT token validation, role checks
- **Request Validation**: Input validation and error responses
- **Response Formatting**: Correct JSON responses
- **Error Handling**: Proper HTTP status codes and error messages

**Example Test Structure**:
```python
class TestUserAPI:
    async def test_create_user_success(self, async_client, admin_token):
        # Test successful user creation via API
        
    async def test_create_user_unauthorized(self, async_client):
        # Test unauthorized access
        
    async def test_create_user_invalid_data(self, async_client, admin_token):
        # Test validation errors via API
```

### 4. End-to-End Tests

**Purpose**: Test complete user workflows
**Scope**: Multi-endpoint workflows and business processes
**Database**: Clean test database for each workflow

**Coverage Areas**:
- **User Registration & Login**: Complete authentication workflows
- **Inventory Management**: Adding items, locations, managing stock
- **Scanner Operations**: Complete scanning workflows
- **Alert Processing**: Alert creation and management workflows

## Test Data Management

### Factory Pattern

Using `factory-boy` for consistent, maintainable test data:

```python
class UserFactory(factory.Factory):
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    hashed_password = factory.LazyFunction(lambda: hash_password("testpass123"))
    role = UserRole.USER
    is_active = True
```

### Fixture Hierarchy

```python
# Database fixtures
@pytest.fixture(scope="session")
def test_engine():
    # Create test database engine

@pytest.fixture
def db_session(test_engine):
    # Provide clean database session for each test

# Authentication fixtures
@pytest.fixture
def admin_user(db_session):
    # Create admin user for tests

@pytest.fixture
def admin_token(admin_user):
    # Generate admin JWT token

# API client fixtures
@pytest.fixture
def async_client():
    # Provide async HTTP client for API tests
```

## Code Coverage Goals

- **Overall Coverage**: Minimum 90%
- **Critical Components**: 95%+ coverage
  - Authentication & Authorization
  - CRUD Operations
  - API Endpoints
- **Business Logic**: 90%+ coverage
- **Utility Functions**: 85%+ coverage

## Test Configuration

### pytest.ini
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --cov=src/stocky_backend
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=90
    --strict-markers
    --disable-warnings
asyncio_mode = auto
markers =
    unit: Unit tests
    integration: Integration tests
    api: API tests
    e2e: End-to-end tests
    slow: Slow running tests
    auth: Authentication related tests
    database: Database related tests
```

## Running Tests

### Basic Test Execution
```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit                    # Unit tests only
pytest -m integration            # Integration tests only
pytest -m api                    # API tests only
pytest -m e2e                    # E2E tests only

# Run specific test files
pytest tests/unit/test_auth.py
pytest tests/api/test_users_api.py

# Run with coverage
pytest --cov=src/stocky_backend --cov-report=html
```

### Parallel Execution
```bash
# Run tests in parallel (faster execution)
pytest -n auto

# Run with specific number of workers
pytest -n 4
```

### Development Workflow
```bash
# Watch mode for development
pytest --looponfail

# Run only failed tests
pytest --lf

# Run failed tests first
pytest --ff
```

## Continuous Integration

### GitHub Actions Configuration
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11, 3.12]
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: |
          pip install -e .
          pip install -r tests/requirements-test.txt
      - name: Run tests
        run: pytest --cov=src/stocky_backend --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Test Quality Standards

### Test Naming Convention
- **Descriptive Names**: `test_create_user_with_valid_email_succeeds`
- **Given-When-Then Structure**: Clear test structure
- **Behavior Focused**: Test what the code should do, not how

### Test Structure
```python
def test_create_user_with_valid_data_succeeds():
    # Given: Setup test data and preconditions
    user_data = UserFactory.build()
    
    # When: Execute the action being tested
    result = user_crud.create(db, obj_in=user_data)
    
    # Then: Assert the expected outcomes
    assert result.id is not None
    assert result.email == user_data.email
    assert result.is_active is True
```

### Assertion Guidelines
- **Single Responsibility**: One test, one concept
- **Clear Assertions**: Explicit, meaningful assertions
- **Error Messages**: Custom error messages for complex assertions

## Mock Strategy

### When to Mock
- **External APIs**: Always mock external service calls
- **File System**: Mock file operations
- **Time-Dependent Code**: Use `freezegun` for time control
- **Expensive Operations**: Mock slow computations

### When NOT to Mock
- **Database in Integration Tests**: Use real database with transactions
- **Internal Application Logic**: Test real interactions
- **Simple Data Structures**: Don't mock basic Python types

## Performance Testing

### Load Testing (Optional)
```python
@pytest.mark.slow
def test_api_performance_under_load():
    # Performance benchmarking for critical endpoints
```

### Database Performance
```python
def test_query_performance(db_session):
    # Test database query performance
    with timer() as t:
        results = user_crud.get_multi(db_session, limit=1000)
    assert t.elapsed < 1.0  # Should complete within 1 second
```

## Security Testing

### Authentication Tests
- JWT token validation
- Password hashing verification
- Role-based access control
- Token expiration handling

### Input Validation Tests
- SQL injection prevention
- XSS prevention
- Input sanitization
- Schema validation

## Maintenance & Evolution

### Adding New Tests
1. **Identify Test Category**: Unit, integration, API, or E2E
2. **Create Test File**: Follow naming conventions
3. **Use Appropriate Fixtures**: Leverage existing test infrastructure
4. **Follow Test Standards**: Maintain code quality standards

### Updating Tests
- **Refactor Incrementally**: Update tests when code changes
- **Maintain Coverage**: Ensure coverage doesn't decrease
- **Update Documentation**: Keep test documentation current

### Performance Monitoring
- **Track Test Duration**: Monitor test execution time
- **Optimize Slow Tests**: Refactor or parallelize slow tests
- **Resource Usage**: Monitor memory and CPU usage during tests

## Troubleshooting

### Common Issues
1. **Database State**: Ensure proper test isolation
2. **Async Issues**: Proper async/await usage in tests
3. **Fixture Scope**: Correct fixture scope selection
4. **Mock Leakage**: Proper mock cleanup between tests

### Debugging Tips
```bash
# Run with verbose output
pytest -v

# Drop into debugger on failure
pytest --pdb

# Show local variables on failure
pytest -l

# Run specific test with output
pytest -s tests/unit/test_auth.py::test_specific_function
```

This comprehensive testing framework ensures robust, maintainable, and thorough testing coverage for the Stocky Backend application while providing clear guidelines for future development and maintenance.
