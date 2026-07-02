"""Unit tests for authentication functionality."""

from src.stocky_backend.core.auth import (
    get_password_hash,
    verify_password,
)
from src.stocky_backend.crud.crud import session as session_crud
from tests.factories.user_factory import UserFactory


class TestPasswordSecurity:
    """Test password hashing and verification."""

    def test_password_hash_and_verify(self):
        """Test password hashing and verification works correctly."""
        password = "test_password_123"
        hashed = get_password_hash(password)
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False

    def test_same_password_different_hashes(self):
        """Test that same password generates different hashes (salt)."""
        password = "test_password_123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

    def test_empty_password_handling(self):
        """Test handling of empty passwords."""
        empty_password = ""
        hashed = get_password_hash(empty_password)
        assert verify_password(empty_password, hashed) is True
        assert verify_password("not_empty", hashed) is False


class TestSessionManagement:
    """Test session creation, lookup, and deletion."""

    def test_create_and_lookup_session(self, db_session):
        """Test creating a session and looking up the user."""
        user = UserFactory.create(
            username="sessionuser",
            email="session@test.com",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        raw_token = session_crud.create(db_session, user_id=user.id)
        assert raw_token is not None
        assert len(raw_token) == 64  # 32 bytes of hex

        found_user = session_crud.get_user_by_token(db_session, raw_token)
        assert found_user is not None
        assert found_user.id == user.id

    def test_lookup_invalid_token(self, db_session):
        """Test looking up a non-existent token returns None."""
        result = session_crud.get_user_by_token(db_session, "nonexistent_token_1234567890")
        assert result is None

    def test_delete_session(self, db_session):
        """Test deleting a session."""
        user = UserFactory.create(
            username="deleteuser",
            email="delete@test.com",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        raw_token = session_crud.create(db_session, user_id=user.id)
        assert session_crud.get_user_by_token(db_session, raw_token) is not None

        result = session_crud.delete(db_session, raw_token)
        assert result is True
        assert session_crud.get_user_by_token(db_session, raw_token) is None

    def test_delete_nonexistent_session(self, db_session):
        """Test deleting a non-existent session returns False."""
        result = session_crud.delete(db_session, "nonexistent_token")
        assert result is False

    def test_delete_all_for_user(self, db_session):
        """Test deleting all sessions for a user."""
        user = UserFactory.create(
            username="clearuser",
            email="clear@test.com",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        token1 = session_crud.create(db_session, user_id=user.id)
        token2 = session_crud.create(db_session, user_id=user.id)
        assert session_crud.get_user_by_token(db_session, token1) is not None
        assert session_crud.get_user_by_token(db_session, token2) is not None

        count = session_crud.delete_all_for_user(db_session, user.id)
        assert count == 2
        assert session_crud.get_user_by_token(db_session, token1) is None
        assert session_crud.get_user_by_token(db_session, token2) is None

    def test_inactive_user_session(self, db_session):
        """Test sessions for inactive users still resolve (security layer checks is_active)."""
        user = UserFactory.create(
            username="inactive_session",
            email="inactive_sess@test.com",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        raw_token = session_crud.create(db_session, user_id=user.id)

        user.is_active = False
        db_session.commit()

        found_user = session_crud.get_user_by_token(db_session, raw_token)
        assert found_user is not None
        assert found_user.id == user.id
