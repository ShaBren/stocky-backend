"""API tests for authentication endpoints."""

import pytest
from httpx import AsyncClient


class TestAuthenticationAPI:
    """Test authentication API endpoints."""

    @pytest.mark.asyncio
    async def test_login_with_valid_credentials(
        self, async_client: AsyncClient, db_session, regular_user
    ):
        """Test successful login with valid credentials."""
        login_data = {
            "username": regular_user.username,
            "password": "testpassword123",
        }
        response = await async_client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == regular_user.id
        assert data["role"] == "member"
        assert data["username"] == regular_user.username

    @pytest.mark.asyncio
    async def test_login_with_invalid_credentials(self, async_client: AsyncClient, regular_user):
        """Test login failure with invalid credentials."""
        login_data = {"username": regular_user.username, "password": "wrong_password"}
        response = await async_client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_with_nonexistent_user(self, async_client: AsyncClient):
        """Test login failure with non-existent user."""
        login_data = {"username": "nonexistent_user", "password": "any_password"}
        response = await async_client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_with_inactive_user(self, async_client: AsyncClient, inactive_user):
        """Test login failure with inactive user."""
        login_data = {"username": inactive_user.username, "password": "testpassword123"}
        response = await async_client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_with_missing_credentials(self, async_client: AsyncClient):
        """Test login failure with missing credentials."""
        login_data = {"username": "testuser"}
        response = await async_client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_with_empty_credentials(self, async_client: AsyncClient):
        """Test login failure with empty credentials."""
        login_data = {"username": "", "password": ""}
        response = await async_client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code in [401, 422]

    @pytest.mark.asyncio
    async def test_login_json_endpoint(self, async_client: AsyncClient, regular_user):
        """Test login via JSON endpoint."""
        login_data = {
            "username": regular_user.username,
            "password": "testpassword123",
            "remember_me": False,
        }
        response = await async_client.post("/api/v1/auth/login-json", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == regular_user.id
        assert data["role"] == "member"

    @pytest.mark.asyncio
    async def test_login_sets_session_cookie(self, async_client: AsyncClient, regular_user):
        """Test that login sets the session cookie."""
        login_data = {
            "username": regular_user.username,
            "password": "testpassword123",
        }
        response = await async_client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        assert "stocky_session" in response.cookies


class TestProtectedEndpoints:
    """Test access to protected endpoints."""

    @pytest.mark.asyncio
    async def test_access_protected_endpoint_with_valid_session(
        self, async_client: AsyncClient, auth_headers_user
    ):
        """Test accessing protected endpoint with valid session cookie."""
        response = await async_client.get("/api/v1/auth/me", headers=auth_headers_user)
        assert response.status_code == 200
        data = response.json()
        assert "username" in data
        assert "email" in data

    @pytest.mark.asyncio
    async def test_access_protected_endpoint_without_session(self, async_client: AsyncClient):
        """Test accessing protected endpoint without session."""
        response = await async_client.get("/api/v1/auth/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_access_protected_endpoint_with_invalid_cookie(self, async_client: AsyncClient):
        """Test accessing protected endpoint with invalid session cookie."""
        headers = {"Cookie": "stocky_session=invalid_token_value"}
        response = await async_client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_invalidates_session(self, async_client: AsyncClient, user_token):
        """Test that logout invalidates the session."""
        headers = {"Cookie": f"stocky_session={user_token}"}
        response = await async_client.post("/api/v1/auth/logout", headers=headers)
        assert response.status_code == 200

        # After logout, the session should no longer work
        response = await async_client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401


class TestPasswordChange:
    """Test password change functionality."""

    @pytest.mark.asyncio
    async def test_change_password_success(
        self, async_client: AsyncClient, auth_headers_user, regular_user
    ):
        """Test successful password change."""
        data = {
            "current_password": "testpassword123",
            "new_password": "new_password_456",
        }
        response = await async_client.post(
            "/api/v1/auth/change-password", json=data, headers=auth_headers_user
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(
        self, async_client: AsyncClient, auth_headers_user
    ):
        """Test password change with wrong current password."""
        data = {
            "current_password": "wrong_current",
            "new_password": "new_password_456",
        }
        response = await async_client.post(
            "/api/v1/auth/change-password", json=data, headers=auth_headers_user
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_change_password_same_as_current(
        self, async_client: AsyncClient, auth_headers_user
    ):
        """Test password change with same password."""
        data = {
            "current_password": "testpassword123",
            "new_password": "testpassword123",
        }
        response = await async_client.post(
            "/api/v1/auth/change-password", json=data, headers=auth_headers_user
        )
        assert response.status_code == 400


class TestRoleBasedAccess:
    """Test role-based access control."""

    @pytest.mark.asyncio
    async def test_admin_access_to_admin_endpoint(
        self, async_client: AsyncClient, auth_headers_admin
    ):
        """Test admin user accessing admin-only endpoint."""
        response = await async_client.get("/api/v1/users/", headers=auth_headers_admin)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_user_denied_access_to_admin_endpoint(
        self, async_client: AsyncClient, auth_headers_user
    ):
        """Test regular user denied access to admin-only endpoint."""
        response = await async_client.get("/api/v1/users/", headers=auth_headers_user)
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        assert "Access denied" in data["detail"]

    @pytest.mark.asyncio
    async def test_user_access_to_own_data(self, async_client: AsyncClient, auth_headers_user):
        """Test user can access their own data."""
        response = await async_client.get("/api/v1/auth/me", headers=auth_headers_user)

        # Then
        assert response.status_code == 200
        data = response.json()
        assert "username" in data
        assert "email" in data
        assert "role" in data
