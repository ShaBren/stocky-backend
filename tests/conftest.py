"""
Shared pytest configuration and fixtures for Stocky Backend tests.

This module provides common fixtures and configuration used across all test categories.
"""

import asyncio
import os
import tempfile
from typing import AsyncGenerator
from unittest.mock import Mock

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from src.stocky_backend.core.auth import create_access_token
from src.stocky_backend.db.database import Base, get_db
from src.stocky_backend.main import app
from src.stocky_backend.models.models import User, UserRole


# ============================================================================
# Session-scoped fixtures (expensive setup/teardown)
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_db_url():
    """Provide test database URL using in-memory SQLite."""
    return "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_engine(test_db_url):
    """Create test database engine with optimized settings for testing."""
    engine = create_engine(
        test_db_url,
        connect_args={"check_same_thread": False},
        poolclass=None,
        echo=False,  # Set to True for SQL debugging
    )
    
    # Enable foreign key constraints for SQLite
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        if 'sqlite' in str(dbapi_connection):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="session")
def TestingSessionLocal(test_engine):
    """Create session factory for testing."""
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


# ============================================================================
# Function-scoped fixtures (clean state for each test)
# ============================================================================

@pytest.fixture
def db_session(test_engine):
    """
    Provide a clean database session for each test.
    
    Uses transaction rollback to ensure test isolation.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def override_get_db(db_session):
    """Override the get_db dependency with test database session."""
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass  # Session cleanup handled by db_session fixture
    
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def async_client(override_get_db) -> AsyncGenerator[AsyncClient, None]:
    """
    Provide an async HTTP client for API testing.
    
    This client uses the test database and handles proper cleanup.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        yield client


# ============================================================================
# Authentication fixtures
# ============================================================================

@pytest.fixture
def admin_user(db_session) -> User:
    """Create an admin user for testing."""
    from tests.factories.user_factory import UserFactory
    
    user = UserFactory.create(
        username="admin_test",
        email="admin@test.com",
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def regular_user(db_session) -> User:
    """Create a regular user for testing."""
    from tests.factories.user_factory import UserFactory
    
    user = UserFactory.create(
        username="user_test",
        email="user@test.com",
        role=UserRole.MEMBER,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def inactive_user(db_session) -> User:
    """Create an inactive user for testing."""
    from tests.factories.user_factory import UserFactory
    
    user = UserFactory.create(
        username="inactive_test",
        email="inactive@test.com",
        role=UserRole.MEMBER,
        is_active=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_token(admin_user) -> str:
    """Generate JWT token for admin user."""
    return create_access_token(data={"sub": str(admin_user.id)})


@pytest.fixture
def user_token(regular_user) -> str:
    """Generate JWT token for regular user."""
    return create_access_token(data={"sub": str(regular_user.id)})


@pytest.fixture
def auth_headers_admin(admin_token) -> dict:
    """Provide authorization headers for admin user."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def auth_headers_user(user_token) -> dict:
    """Provide authorization headers for regular user."""
    return {"Authorization": f"Bearer {user_token}"}


# ============================================================================
# Mock fixtures
# ============================================================================

@pytest.fixture
def mock_settings():
    """Provide mock settings for testing."""
    settings = Mock()
    settings.DATABASE_URL = "sqlite:///:memory:"
    settings.SECRET_KEY = "test-secret-key-for-testing-only"
    settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30
    settings.ALGORITHM = "HS256"
    settings.API_V1_STR = "/api/v1"
    return settings


@pytest.fixture
def temp_file():
    """Provide a temporary file for testing file operations."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        yield tmp.name
    os.unlink(tmp.name)


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


# ============================================================================
# Test data fixtures
# ============================================================================

@pytest.fixture
def sample_user_data():
    """Provide sample user data for testing."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "role": UserRole.MEMBER,
        "is_active": True
    }


@pytest.fixture
def sample_item_data():
    """Provide sample item data for testing."""
    return {
        "name": "Test Item",
        "description": "A test item for unit testing",
        "barcode": "1234567890123",
        "category": "Test Category",
        "unit_price": 9.99,
        "is_active": True
    }


@pytest.fixture
def sample_location_data():
    """Provide sample location data for testing."""
    return {
        "name": "Test Location",
        "description": "A test location for unit testing",
        "location_type": "WAREHOUSE",
        "is_active": True
    }


# ============================================================================
# Utility fixtures
# ============================================================================

@pytest.fixture
def capture_logs(caplog):
    """Capture and provide access to log messages during tests."""
    caplog.set_level("DEBUG")
    return caplog


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables after each test."""
    original_env = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(original_env)


# ============================================================================
# Pytest hooks and configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Register custom markers
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "api: API tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "auth: Authentication tests")
    config.addinivalue_line("markers", "database: Database tests")
    config.addinivalue_line("markers", "external: External service tests")
    config.addinivalue_line("markers", "security: Security tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add markers based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "api" in str(item.fspath):
            item.add_marker(pytest.mark.api)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        
        # Add auth marker for auth-related tests
        if "auth" in str(item.fspath) or "auth" in item.name:
            item.add_marker(pytest.mark.auth)
        
        # Add database marker for database tests
        if any(marker in str(item.fspath) for marker in ["database", "crud", "models"]):
            item.add_marker(pytest.mark.database)


@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Perform cleanup after each test."""
    yield
    # Clear any dependency overrides
    app.dependency_overrides.clear()
