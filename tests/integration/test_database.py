"""Integration tests for database operations."""

import pytest
from sqlalchemy.orm import Session

from src.stocky_backend.crud import crud
from src.stocky_backend.models.models import UserRole
from src.stocky_backend.schemas.schemas import UserCreate, UserUpdate
from tests.factories.user_factory import UserFactory


class TestUserCRUDIntegration:
    """Test user CRUD operations with real database."""
    
    def test_create_user_integration(self, db_session: Session):
        """Test creating a user with database integration."""
        # Given
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpassword123"
        )
        
        # When
        created_user = crud.user.create(db=db_session, obj_in=user_data)
        
        # Then
        assert created_user.id is not None
        assert created_user.username == "testuser"
        assert created_user.email == "test@example.com"
        assert created_user.role == UserRole.MEMBER
        assert created_user.is_active is True
        assert created_user.hashed_password is not None
        assert created_user.hashed_password != "testpassword123"  # Should be hashed
    
    def test_get_user_by_id_integration(self, db_session: Session):
        """Test retrieving user by ID with database integration."""
        # Given
        user = UserFactory.create(username="testuser", email="test@example.com")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # When
        retrieved_user = crud.user.get(db=db_session, id=user.id)
        
        # Then
        assert retrieved_user is not None
        assert retrieved_user.id == user.id
        assert retrieved_user.username == "testuser"
        assert retrieved_user.email == "test@example.com"
    
    def test_get_user_by_username_integration(self, db_session: Session):
        """Test retrieving user by username with database integration."""
        # Given
        user = UserFactory.create(username="testuser", email="test@example.com")
        db_session.add(user)
        db_session.commit()
        
        # When
        retrieved_user = crud.user.get_by_username(db=db_session, username="testuser")
        
        # Then
        assert retrieved_user is not None
        assert retrieved_user.username == "testuser"
        assert retrieved_user.email == "test@example.com"
    
    def test_get_user_by_email_integration(self, db_session: Session):
        """Test retrieving user by email with database integration."""
        # Given
        user = UserFactory.create(username="testuser", email="test@example.com")
        db_session.add(user)
        db_session.commit()
        
        # When
        retrieved_user = crud.user.get_by_email(db=db_session, email="test@example.com")
        
        # Then
        assert retrieved_user is not None
        assert retrieved_user.username == "testuser"
        assert retrieved_user.email == "test@example.com"
    
    def test_update_user_integration(self, db_session: Session):
        """Test updating user with database integration."""
        # Given
        user = UserFactory.create(
            username="testuser",
            email="old@example.com"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        update_data = UserUpdate(
            email="new@example.com"
        )
        
        # When
        updated_user = crud.user.update(
            db=db_session,
            db_obj=user,
            obj_in=update_data
        )
        
        # Then
        assert updated_user.id == user.id
        assert updated_user.username == "testuser"  # Unchanged
        assert updated_user.email == "new@example.com"  # Updated
    
    def test_delete_user_integration(self, db_session: Session):
        """Test deleting user with database integration."""
        # Given
        user = UserFactory.create(username="testuser", email="test@example.com")
        db_session.add(user)
        db_session.commit()
        user_id = user.id
        
        # When
        deleted_user = crud.user.remove(db=db_session, id=user_id)
        
        # Then
        assert deleted_user.id == user_id
        
        # Verify user is actually deleted
        retrieved_user = crud.user.get(db=db_session, id=user_id)
        assert retrieved_user is None
    
    def test_get_multi_users_integration(self, db_session: Session):
        """Test retrieving multiple users with database integration."""
        # Given
        users = [
            UserFactory.create(username=f"user{i}", email=f"user{i}@example.com")
            for i in range(5)
        ]
        for user in users:
            db_session.add(user)
        db_session.commit()
        
        # When
        retrieved_users = crud.user.get_multi(db=db_session, skip=0, limit=10)
        
        # Then
        assert len(retrieved_users) >= 5
        usernames = [user.username for user in retrieved_users]
        for i in range(5):
            assert f"user{i}" in usernames
    
    def test_user_authentication_integration(self, db_session: Session):
        """Test user authentication with database integration."""
        # Given
        password = "testpassword123"
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password=password,
        )
        created_user = crud.user.create(db=db_session, obj_in=user_data)
        
        # When
        from src.stocky_backend.core.auth import authenticate_user
        authenticated_user = authenticate_user(
            db=db_session,
            username="testuser",
            password=password
        )
        
        # Then
        assert authenticated_user is not False
        assert authenticated_user.id == created_user.id
        assert authenticated_user.username == "testuser"
    
    def test_user_authentication_wrong_password_integration(self, db_session: Session):
        """Test user authentication with wrong password and database integration."""
        # Given
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="correct_password",
        )
        crud.user.create(db=db_session, obj_in=user_data)
        
        # When
        from src.stocky_backend.core.auth import authenticate_user
        authenticated_user = authenticate_user(
            db=db_session,
            username="testuser",
            password="wrong_password"
        )
        
        # Then
        assert authenticated_user is False


class TestUserConstraintsIntegration:
    """Test database constraints and validations."""
    
    def test_unique_username_constraint(self, db_session: Session):
        """Test that duplicate usernames are not allowed."""
        # Given
        user1_data = UserCreate(
            username="testuser",
            email="user1@example.com",
            password="password123",
        )
        user2_data = UserCreate(
            username="testuser",  # Same username
            email="user2@example.com",
            password="password123",
        )
        
        # When
        crud.user.create(db=db_session, obj_in=user1_data)
        
        # Then
        with pytest.raises(Exception):  # Should raise integrity error
            crud.user.create(db=db_session, obj_in=user2_data)
    
    def test_unique_email_constraint(self, db_session: Session):
        """Test that duplicate emails are not allowed."""
        # Given
        user1_data = UserCreate(
            username="user1",
            email="same@example.com",
            password="password123",
        )
        user2_data = UserCreate(
            username="user2",
            email="same@example.com",  # Same email
            password="password123",
        )
        
        # When
        crud.user.create(db=db_session, obj_in=user1_data)
        
        # Then
        with pytest.raises(Exception):  # Should raise integrity error
            crud.user.create(db=db_session, obj_in=user2_data)


class TestDatabaseTransactions:
    """Test database transaction handling."""
    
    def test_rollback_on_error(self, db_session: Session):
        """Test that database transactions are properly rolled back on error."""
        # Given
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="password123",
        )
        
        # Create initial user
        initial_user = crud.user.create(db=db_session, obj_in=user_data)
        initial_count = len(crud.user.get_multi(db=db_session))
        
        # When - Try to create duplicate user (should fail)
        try:
            duplicate_data = UserCreate(
                username="testuser",  # Duplicate username
                email="duplicate@example.com",
                password="password123",
            )
            crud.user.create(db=db_session, obj_in=duplicate_data)
        except Exception:
            db_session.rollback()
        
        # Then
        final_count = len(crud.user.get_multi(db=db_session))
        assert final_count == initial_count  # Count should be unchanged
        
        # Original user should still exist
        original_user = crud.user.get(db=db_session, id=initial_user.id)
        assert original_user is not None
        assert original_user.username == "testuser"


class TestUserActivationIntegration:
    """Test user activation/deactivation with database integration."""
    
    def test_deactivate_user_integration(self, db_session: Session):
        """Test deactivating a user with database integration."""
        # Given
        user = UserFactory.create(username="testuser", is_active=True)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # When
        update_data = UserUpdate(is_active=False)
        updated_user = crud.user.update(
            db=db_session,
            db_obj=user,
            obj_in=update_data
        )
        
        # Then
        assert updated_user.is_active is False
        
        # Verify in database
        db_user = crud.user.get(db=db_session, id=user.id)
        assert db_user.is_active is False
    
    def test_inactive_user_authentication_integration(self, db_session: Session):
        """Test that inactive users cannot authenticate."""
        # Given
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="password123",
        )
        created_user = crud.user.create(db=db_session, obj_in=user_data)
        
        # Deactivate user
        update_data = UserUpdate(is_active=False)
        crud.user.update(db=db_session, db_obj=created_user, obj_in=update_data)
        
        # When
        from src.stocky_backend.core.auth import authenticate_user
        authenticated_user = authenticate_user(
            db=db_session,
            username="testuser",
            password="password123"
        )
        
        # Then
        assert authenticated_user is False
