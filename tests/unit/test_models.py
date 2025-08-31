"""Unit tests for SQLAlchemy models."""

import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from src.stocky_backend.models.models import User, UserRole, Item, Location
from tests.factories.user_factory import UserFactory


class TestUserModel:
    """Test User model functionality."""
    
    def test_user_creation_with_required_fields(self, db_session):
        """Test creating user with minimum required fields."""
        # Given
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password_here",
            role=UserRole.MEMBER
        )
        
        # When
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Then
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == UserRole.MEMBER
        assert user.is_active is True  # Default value
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)  # Both timestamps are set on creation
    
    def test_user_creation_with_all_fields(self, db_session):
        """Test creating user with all fields populated."""
        # Given
        user = User(
            username="fulluser",
            email="full@example.com",
            hashed_password="hashed_password_here",
            role=UserRole.ADMIN,
            is_active=False
        )
        
        # When
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Then
        assert user.username == "fulluser"
        assert user.email == "full@example.com"
        assert user.role == UserRole.ADMIN
        assert user.is_active is False
    
    def test_user_string_representation(self, db_session):
        """Test user string representation."""
        # Given
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password_here"
        )
        
        # When
        str_repr = str(user)
        
        # Then
        assert "testuser" in str_repr
    
    def test_username_uniqueness_constraint(self, db_session):
        """Test that usernames must be unique."""
        # Given
        user1 = User(
            username="testuser",
            email="user1@example.com",
            hashed_password="password1"
        )
        user2 = User(
            username="testuser",  # Same username
            email="user2@example.com",
            hashed_password="password2"
        )
        
        # When
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        
        # Then
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_email_uniqueness_constraint(self, db_session):
        """Test that emails must be unique."""
        # Given
        user1 = User(
            username="user1",
            email="same@example.com",
            hashed_password="password1"
        )
        user2 = User(
            username="user2",
            email="same@example.com",  # Same email
            hashed_password="password2"
        )
        
        # When
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        
        # Then
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_user_role_enum_values(self, db_session):
        """Test that user role accepts only valid enum values."""
        # Given/When/Then - Valid roles
        for role in [UserRole.MEMBER, UserRole.ADMIN, UserRole.SCANNER, UserRole.READ_ONLY]:
            user = User(
                username=f"user_{role.value}",
                email=f"user_{role.value}@example.com",
                hashed_password="password",
                role=role
            )
            db_session.add(user)
            db_session.commit()
            assert user.role == role
            db_session.delete(user)  # Clean up
            db_session.commit()
    
    def test_user_timestamps(self, db_session):
        """Test that timestamps are properly managed."""
        # Given
        user = User(
            username="timestampuser",
            email="timestamp@example.com",
            hashed_password="password"
        )
        
        # When - Create user
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        created_time = user.created_at
        
        # Then - Created timestamp should be set
        assert created_time is not None
        assert isinstance(user.updated_at, datetime)  # Updated timestamp is also set on creation
        
        # When - Update user
        user.username = "updated_user"  # Update a field that actually exists
        db_session.commit()
        db_session.refresh(user)
        
        # Then - Updated timestamp should change
        assert user.updated_at is not None
        assert user.updated_at >= created_time  # Should be same or greater
        assert user.created_at == created_time  # Created time unchanged
    
    def test_user_factory_integration(self, db_session):
        """Test that UserFactory works correctly with the model."""
        # Given/When
        user = UserFactory.create(username="factoryuser", email="factory@example.com")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Then
        assert user.id is not None
        assert user.username == "factoryuser"
        assert user.email == "factory@example.com"
        assert user.role == UserRole.MEMBER  # Default from factory
        assert user.is_active is True  # Default from factory
        assert user.hashed_password is not None


class TestUserModelValidation:
    """Test User model validation and constraints."""
    
    def test_required_username_field(self, db_session):
        """Test that username is required."""
        # Given
        user = User(
            # username missing
            email="test@example.com",
            hashed_password="password"
        )
        
        # When/Then
        db_session.add(user)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_required_email_field(self, db_session):
        """Test that email is required."""
        # Given
        user = User(
            username="testuser",
            # email missing
            hashed_password="password"
        )
        
        # When/Then
        db_session.add(user)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_required_hashed_password_field(self, db_session):
        """Test that hashed_password is required."""
        # Given
        user = User(
            username="testuser",
            email="test@example.com"
            # hashed_password missing
        )
        
        # When/Then
        db_session.add(user)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_default_values(self, db_session):
        """Test model default values."""
        # Given
        user = User(
            username="defaultuser",
            email="default@example.com",
            hashed_password="password"
            # Not specifying role or is_active
        )
        
        # When
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Then
        assert user.role == UserRole.MEMBER  # Default role
        assert user.is_active is True  # Default active state


class TestItemModel:
    """Test Item model functionality."""
    
    def test_item_creation_with_required_fields(self, db_session):
        """Test creating item with minimum required fields."""
        # Given
        user = User(username="testuser", email="test@example.com", hashed_password="password")
        db_session.add(user)
        db_session.commit()
        
        item = Item(
            name="Test Item",
            description="A test item",
            upc="1234567890123",
            created_by=user.id
        )
        
        # When
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)
        
        # Then
        assert item.id is not None
        assert item.name == "Test Item"
        assert item.description == "A test item"
        assert item.upc == "1234567890123"
        assert item.is_active is True  # Default value
        assert isinstance(item.created_at, datetime)
    
    def test_item_barcode_uniqueness(self, db_session):
        """Test that item UPCs must be unique."""
        # Given
        user = User(username="testuser", email="test@example.com", hashed_password="password")
        db_session.add(user)
        db_session.commit()
        
        item1 = Item(
            name="Item 1",
            description="First item",
            upc="1234567890123",
            created_by=user.id
        )
        item2 = Item(
            name="Item 2",
            description="Second item",
            upc="1234567890123",  # Same UPC
            created_by=user.id
        )
        
        # When
        db_session.add(item1)
        db_session.commit()
        
        db_session.add(item2)
        
        # Then
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_item_with_optional_fields(self, db_session):
        """Test item creation with optional fields."""
        # Given
        user = User(username="testuser", email="test@example.com", hashed_password="password")
        db_session.add(user)
        db_session.commit()
        
        item = Item(
            name="Complete Item",
            description="An item with all fields",
            upc="9876543210987",
            default_storage_type="PANTRY",
            is_active=False,
            created_by=user.id
        )
        
        # When
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)
        
        # Then
        assert item.default_storage_type == "PANTRY"
        assert item.is_active is False


class TestLocationModel:
    """Test Location model functionality."""
    
    def test_location_creation(self, db_session):
        """Test creating location with required fields."""
        # Given
        user = User(username="testuser", email="test@example.com", hashed_password="password")
        db_session.add(user)
        db_session.commit()
        
        location = Location(
            name="Test Location",
            description="A test location",
            storage_type="PANTRY",
            created_by=user.id
        )
        
        # When
        db_session.add(location)
        db_session.commit()
        db_session.refresh(location)
        
        # Then
        assert location.id is not None
        assert location.name == "Test Location"
        assert location.description == "A test location"
        assert location.storage_type == "PANTRY"
        assert location.is_active is True  # Default value
    
    def test_location_name_uniqueness(self, db_session):
        """Test that multiple locations can have the same name (no unique constraint)."""
        # Given
        user = User(username="testuser", email="test@example.com", hashed_password="password")
        db_session.add(user)
        db_session.commit()
        
        location1 = Location(
            name="Same Location",
            description="First location",
            storage_type="PANTRY",
            created_by=user.id
        )
        location2 = Location(
            name="Same Location",  # Same name - this should be allowed
            description="Second location",
            storage_type="FREEZER",
            created_by=user.id
        )
        
        # When
        db_session.add(location1)
        db_session.commit()
        
        db_session.add(location2)
        db_session.commit()  # This should succeed
        
        # Then
        assert location1.id is not None
        assert location2.id is not None
        assert location1.name == location2.name


class TestModelRelationships:
    """Test model relationships and foreign keys."""
    
    def test_user_item_relationship(self, db_session):
        """Test relationships between users and items (if any)."""
        # This would depend on your actual model relationships
        # Example: if items have a created_by_user relationship
        pass
    
    def test_cascade_behavior(self, db_session):
        """Test cascade delete behavior."""
        # This would test what happens when a parent record is deleted
        # Example: when a user is deleted, what happens to their items?
        pass
