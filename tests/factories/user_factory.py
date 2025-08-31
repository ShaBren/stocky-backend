"""User factory for generating test data."""

import factory
from factory import LazyAttribute, Sequence

from src.stocky_backend.core.auth import get_password_hash
from src.stocky_backend.models.models import User, UserRole


class UserFactory(factory.Factory):
    """Factory for creating User instances for testing."""
    
    class Meta:
        model = User
    
    # Basic user attributes
    username = Sequence(lambda n: f"user{n}")
    email = LazyAttribute(lambda obj: f"{obj.username}@example.com")
    
    # Password handling
    hashed_password = factory.LazyFunction(
        lambda: get_password_hash("testpassword123")
    )
    
    # Default role and status
    role = UserRole.MEMBER
    is_active = True
    
    @classmethod
    def create_admin(cls, **kwargs):
        """Create an admin user."""
        defaults = {
            "role": UserRole.ADMIN,
            "username": "admin",
            "email": "admin@example.com"
        }
        defaults.update(kwargs)
        return cls(**defaults)
    
    @classmethod
    def create_member(cls, **kwargs):
        """Create a member user."""
        defaults = {
            "role": UserRole.MEMBER,
            "username": "member",
            "email": "member@example.com"
        }
        defaults.update(kwargs)
        return cls(**defaults)
    
    @classmethod
    def create_inactive(cls, **kwargs):
        """Create an inactive user."""
        defaults = {
            "is_active": False,
            "username": "inactive",
            "email": "inactive@example.com"
        }
        defaults.update(kwargs)
        return cls(**defaults)
    
    @classmethod
    def create_with_custom_password(cls, password: str, **kwargs):
        """Create a user with a custom password."""
        kwargs["hashed_password"] = get_password_hash(password)
        return cls(**kwargs)
