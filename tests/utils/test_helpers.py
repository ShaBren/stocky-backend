"""Test helper functions and utilities."""

import asyncio
import time
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

from httpx import AsyncClient
from sqlalchemy.orm import Session

from src.stocky_backend.models.models import User


class TimerHelper:
    """Helper class for timing test operations."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.elapsed = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.elapsed = self.end_time - self.start_time


@contextmanager
def timer():
    """Simple timer context manager for performance testing."""
    t = TimerHelper()
    yield t.__enter__()
    t.__exit__(None, None, None)


async def create_test_user(
    async_client: AsyncClient,
    admin_headers: Dict[str, str],
    username: str = "testuser",
    email: str = "test@example.com",
    password: str = "testpass123",
    **kwargs
) -> Dict[str, Any]:
    """Helper to create a test user via API."""
    user_data = {
        "username": username,
        "email": email,
        "password": password,
        "full_name": f"Test User {username}",
        "role": "USER",
        **kwargs
    }
    
    response = await async_client.post(
        "/api/v1/users/",
        json=user_data,
        headers=admin_headers
    )
    
    assert response.status_code == 201
    return response.json()


async def login_user(
    async_client: AsyncClient,
    username: str,
    password: str
) -> str:
    """Helper to login a user and return access token."""
    login_data = {
        "username": username,
        "password": password
    }
    
    response = await async_client.post(
        "/api/v1/auth/login",
        data=login_data
    )
    
    assert response.status_code == 200
    return response.json()["access_token"]


def get_auth_headers(token: str) -> Dict[str, str]:
    """Helper to create authorization headers from token."""
    return {"Authorization": f"Bearer {token}"}


async def cleanup_test_users(
    async_client: AsyncClient,
    admin_headers: Dict[str, str],
    usernames: List[str]
) -> None:
    """Helper to cleanup test users after tests."""
    # Get all users
    response = await async_client.get(
        "/api/v1/users/",
        headers=admin_headers
    )
    
    if response.status_code == 200:
        all_users = response.json()
        for user in all_users:
            if user["username"] in usernames:
                await async_client.delete(
                    f"/api/v1/users/{user['id']}",
                    headers=admin_headers
                )


def assert_user_response_structure(user_data: Dict[str, Any]) -> None:
    """Assert that user response has expected structure."""
    required_fields = [
        "id", "username", "email", "full_name", 
        "role", "is_active", "created_at"
    ]
    
    for field in required_fields:
        assert field in user_data, f"Missing field: {field}"
    
    # Check field types
    assert isinstance(user_data["id"], int)
    assert isinstance(user_data["username"], str)
    assert isinstance(user_data["email"], str)
    assert isinstance(user_data["is_active"], bool)
    assert user_data["role"] in ["USER", "ADMIN"]
    
    # Ensure sensitive data is not exposed
    assert "password" not in user_data
    assert "hashed_password" not in user_data


def assert_error_response_structure(error_data: Dict[str, Any]) -> None:
    """Assert that error response has expected structure."""
    assert "detail" in error_data
    assert isinstance(error_data["detail"], (str, list, dict))


async def wait_for_condition(
    condition_func,
    timeout: float = 5.0,
    interval: float = 0.1
) -> bool:
    """Wait for a condition to become true within timeout."""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if await condition_func() if asyncio.iscoroutinefunction(condition_func) else condition_func():
            return True
        await asyncio.sleep(interval)
    
    return False


def create_batch_users_data(count: int, prefix: str = "user") -> List[Dict[str, Any]]:
    """Create test data for batch user creation."""
    return [
        {
            "username": f"{prefix}{i}",
            "email": f"{prefix}{i}@example.com",
            "password": f"password{i}",
            "full_name": f"Test User {i}",
            "role": "USER"
        }
        for i in range(count)
    ]


class DatabaseTestHelper:
    """Helper class for database operations in tests."""
    
    @staticmethod
    def count_users(db_session: Session) -> int:
        """Count total users in database."""
        from src.stocky_backend.models.models import User
        return db_session.query(User).count()
    
    @staticmethod
    def get_user_by_username(db_session: Session, username: str) -> Optional[User]:
        """Get user by username from database."""
        from src.stocky_backend.models.models import User
        return db_session.query(User).filter(User.username == username).first()
    
    @staticmethod
    def clear_test_users(db_session: Session, exclude_usernames: List[str] = None) -> None:
        """Clear test users from database, excluding specified usernames."""
        if exclude_usernames is None:
            exclude_usernames = []
        
        from src.stocky_backend.models.models import User
        users_to_delete = db_session.query(User).filter(
            ~User.username.in_(exclude_usernames)
        ).all()
        
        for user in users_to_delete:
            db_session.delete(user)
        db_session.commit()


class APITestHelper:
    """Helper class for API testing operations."""
    
    @staticmethod
    async def get_user_count(
        async_client: AsyncClient,
        admin_headers: Dict[str, str]
    ) -> int:
        """Get total user count via API."""
        response = await async_client.get(
            "/api/v1/users/",
            headers=admin_headers
        )
        
        if response.status_code == 200:
            return len(response.json())
        return 0
    
    @staticmethod
    async def user_exists(
        async_client: AsyncClient,
        admin_headers: Dict[str, str],
        username: str
    ) -> bool:
        """Check if user exists via API."""
        response = await async_client.get(
            "/api/v1/users/",
            headers=admin_headers
        )
        
        if response.status_code == 200:
            users = response.json()
            return any(user["username"] == username for user in users)
        return False
    
    @staticmethod
    async def wait_for_user_creation(
        async_client: AsyncClient,
        admin_headers: Dict[str, str],
        username: str,
        timeout: float = 5.0
    ) -> bool:
        """Wait for user to be created and available via API."""
        async def check_user():
            return await APITestHelper.user_exists(
                async_client, admin_headers, username
            )
        
        return await wait_for_condition(check_user, timeout)


def generate_test_email(username: str, domain: str = "example.com") -> str:
    """Generate a test email address."""
    return f"{username}@{domain}"


def generate_strong_password(length: int = 12) -> str:
    """Generate a strong test password."""
    import string
    import secrets
    
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def mask_sensitive_data(data: Dict[str, Any], fields: List[str] = None) -> Dict[str, Any]:
    """Mask sensitive fields in test data for logging."""
    if fields is None:
        fields = ["password", "hashed_password", "access_token", "token"]
    
    masked_data = data.copy()
    for field in fields:
        if field in masked_data:
            masked_data[field] = "***MASKED***"
    
    return masked_data


class TestDataValidator:
    """Validator for test data integrity."""
    
    @staticmethod
    def validate_user_data(user_data: Dict[str, Any]) -> List[str]:
        """Validate user data and return list of validation errors."""
        errors = []
        
        # Required fields
        required_fields = ["username", "email", "password"]
        for field in required_fields:
            if field not in user_data or not user_data[field]:
                errors.append(f"Missing required field: {field}")
        
        # Email format validation (basic)
        if "email" in user_data and "@" not in user_data["email"]:
            errors.append("Invalid email format")
        
        # Password strength (basic)
        if "password" in user_data and len(user_data["password"]) < 8:
            errors.append("Password too short (minimum 8 characters)")
        
        # Username format
        if "username" in user_data:
            username = user_data["username"]
            if not username.isalnum():
                errors.append("Username must be alphanumeric")
            if len(username) < 3:
                errors.append("Username too short (minimum 3 characters)")
        
        return errors
    
    @staticmethod
    def is_valid_user_data(user_data: Dict[str, Any]) -> bool:
        """Check if user data is valid."""
        return len(TestDataValidator.validate_user_data(user_data)) == 0
