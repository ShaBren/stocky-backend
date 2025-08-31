"""Unit tests for authentication functionality."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from src.stocky_backend.core.auth import (
    authenticate_user,
    get_current_user,
    verify_token
)
from src.stocky_backend.core.auth import (
    create_access_token,
    get_password_hash,
    verify_password
)
from tests.factories.user_factory import UserFactory


class TestPasswordSecurity:
    """Test password hashing and verification."""
    
    def test_password_hash_and_verify(self):
        """Test password hashing and verification works correctly."""
        # Given
        password = "test_password_123"
        
        # When
        hashed = get_password_hash(password)
        
        # Then
        assert hashed != password  # Should be hashed
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False
    
    def test_same_password_different_hashes(self):
        """Test that same password generates different hashes (salt)."""
        # Given
        password = "test_password_123"
        
        # When
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Then
        assert hash1 != hash2  # Different due to salt
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True
    
    def test_empty_password_handling(self):
        """Test handling of empty passwords."""
        # Given
        empty_password = ""
        
        # When
        hashed = get_password_hash(empty_password)
        
        # Then
        assert verify_password(empty_password, hashed) is True
        assert verify_password("not_empty", hashed) is False


class TestJWTTokens:
    """Test JWT token creation and validation."""
    
    def test_create_access_token_with_username(self):
        """Test creating access token with username data."""
        # Given
        username = "testuser"
        data = {"sub": username}
        
        # When
        token = create_access_token(data=data)
        
        # Then
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_access_token_with_expiration(self):
        """Test creating access token with custom expiration."""
        # Given
        username = "testuser"
        data = {"sub": username}
        expires_delta = timedelta(minutes=15)
        
        # When
        token = create_access_token(data=data, expires_delta=expires_delta)
        
        # Then
        assert token is not None
        assert isinstance(token, str)
    
    @patch('src.stocky_backend.core.auth.jwt')
    def test_token_contains_expected_claims(self, mock_jwt):
        """Test that token contains expected JWT claims."""
        # Given
        username = "testuser"
        data = {"sub": username}
        mock_jwt.encode.return_value = "mocked_token"
        
        # When
        create_access_token(data=data)
        
        # Then
        # Verify jwt.encode was called with correct parameters
        mock_jwt.encode.assert_called_once()
        payload = mock_jwt.encode.call_args[0][0]
        
        assert payload["sub"] == username
        assert "exp" in payload
        assert isinstance(payload["exp"], datetime)


class TestUserAuthentication:
    """Test user authentication logic."""
    
    def test_authenticate_user_with_valid_credentials(self, db_session):
        """Test successful user authentication."""
        # Given
        password = "testpassword123"
        user = UserFactory.create_with_custom_password(
            password=password,
            username="testuser",
            email="test@example.com",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        # Mock the database query
        with patch('src.stocky_backend.crud.crud.user.get_by_username') as mock_get:
            mock_get.return_value = user
            
            # When
            authenticated_user = authenticate_user(
                db=db_session,
                username="testuser",
                password=password
            )
        
        # Then
        assert authenticated_user is not None
        assert authenticated_user.username == "testuser"
        assert authenticated_user.email == "test@example.com"
    
    def test_authenticate_user_with_invalid_password(self, db_session):
        """Test authentication failure with wrong password."""
        # Given
        user = UserFactory.create_with_custom_password(
            password="correct_password",
            username="testuser",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        # Mock the database query
        with patch('src.stocky_backend.crud.crud.user.get_by_username') as mock_get:
            mock_get.return_value = user
            
            # When
            authenticated_user = authenticate_user(
                db=db_session,
                username="testuser",
                password="wrong_password"
            )
        
        # Then
        assert authenticated_user is False
    
    def test_authenticate_user_with_nonexistent_user(self, db_session):
        """Test authentication failure with non-existent user."""
        # Given
        # Mock the database query to return None
        with patch('src.stocky_backend.crud.crud.user.get_by_username') as mock_get:
            mock_get.return_value = None
            
            # When
            authenticated_user = authenticate_user(
                db=db_session,
                username="nonexistent",
                password="any_password"
            )
        
        # Then
        assert authenticated_user is False
    
    def test_authenticate_inactive_user(self, db_session):
        """Test authentication failure with inactive user."""
        # Given
        password = "testpassword123"
        user = UserFactory.create_with_custom_password(
            password=password,
            username="inactive_user",
            is_active=False
        )
        db_session.add(user)
        db_session.commit()
        
        # Mock the database query
        with patch('src.stocky_backend.crud.crud.user.get_by_username') as mock_get:
            mock_get.return_value = user
            
            # When
            authenticated_user = authenticate_user(
                db=db_session,
                username="inactive_user",
                password=password
            )
        
        # Then
        assert authenticated_user is False


class TestTokenVerification:
    """Test JWT token verification and user extraction."""
    
    @patch('src.stocky_backend.core.auth.jwt')
    @patch('src.stocky_backend.crud.crud.user.get_by_username')
    def test_verify_valid_token(self, mock_get_user, mock_jwt, db_session):
        """Test verification of valid JWT token."""
        # Given
        username = "testuser"
        mock_jwt.decode.return_value = {"sub": username}
        user = UserFactory.create(username=username, is_active=True)
        mock_get_user.return_value = user
        
        # When
        result = verify_token("valid_token", db_session)
        
        # Then
        assert result == user
        mock_jwt.decode.assert_called_once()
        mock_get_user.assert_called_once_with(db_session, username=username)
    
    @patch('src.stocky_backend.core.auth.jwt')
    def test_verify_invalid_token(self, mock_jwt, db_session):
        """Test verification of invalid JWT token."""
        # Given
        from jose import JWTError
        mock_jwt.decode.side_effect = JWTError("Invalid token")
        
        # When
        result = verify_token("invalid_token", db_session)
        
        # Then
        assert result is None
    
    @patch('src.stocky_backend.core.auth.jwt')
    @patch('src.stocky_backend.crud.crud.user.get_by_username')
    def test_verify_token_user_not_found(self, mock_get_user, mock_jwt, db_session):
        """Test token verification when user doesn't exist."""
        # Given
        username = "nonexistent"
        mock_jwt.decode.return_value = {"sub": username}
        mock_get_user.return_value = None
        
        # When
        result = verify_token("valid_token", db_session)
        
        # Then
        assert result is None
    
    @patch('src.stocky_backend.core.auth.jwt')
    def test_verify_token_missing_subject(self, mock_jwt, db_session):
        """Test token verification with missing subject claim."""
        # Given
        mock_jwt.decode.return_value = {"exp": 1234567890}  # No 'sub' claim
        
        # When
        result = verify_token("token_without_sub", db_session)
        
        # Then
        assert result is None


class TestCurrentUserExtraction:
    """Test current user extraction from requests."""
    
    @pytest.mark.asyncio
    async def test_get_current_user_with_valid_token(self, db_session):
        """Test extracting current user from valid token."""
        # Given
        user = UserFactory.create(username="testuser", is_active=True)
        
        with patch('src.stocky_backend.core.auth.verify_token') as mock_verify:
            mock_verify.return_value = user
            
            # When
            current_user = await get_current_user(
                db=db_session,
                token="valid_token"
            )
        
        # Then
        assert current_user == user
    
    @pytest.mark.asyncio
    async def test_get_current_user_with_invalid_token(self, db_session):
        """Test current user extraction with invalid token."""
        # Given
        with patch('src.stocky_backend.core.auth.verify_token') as mock_verify:
            mock_verify.return_value = None
            
            # When/Then
            with pytest.raises(Exception):  # Should raise credentials exception
                await get_current_user(
                    db=db_session,
                    token="invalid_token"
                )
    
    @pytest.mark.asyncio
    async def test_get_current_user_with_inactive_user(self, db_session):
        """Test current user extraction with inactive user."""
        # Given
        user = UserFactory.create(username="testuser", is_active=False)
        
        with patch('src.stocky_backend.core.auth.verify_token') as mock_verify:
            mock_verify.return_value = user
            
            # When/Then
            with pytest.raises(Exception):  # Should raise inactive user exception
                await get_current_user(
                    db=db_session,
                    token="valid_token"
                )
