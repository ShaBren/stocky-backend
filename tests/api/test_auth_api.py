"""API tests for authentication endpoints."""

import pytest
from httpx import AsyncClient


class TestAuthenticationAPI:
    """Test authentication API endpoints."""
    
    @pytest.mark.asyncio
    async def test_login_with_valid_credentials(
        self, 
        async_client: AsyncClient, 
        db_session,
        regular_user
    ):
        """Test successful login with valid credentials."""
        # Given
        login_data = {
            "username": regular_user.username,
            "password": "testpassword123"  # Default password from factory
        }
        
        # When
        response = await async_client.post(
            "/api/v1/auth/login",
            data=login_data
        )
        
        # Then
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["access_token"] is not None
    
    @pytest.mark.asyncio
    async def test_login_with_invalid_credentials(
        self, 
        async_client: AsyncClient,
        regular_user
    ):
        """Test login failure with invalid credentials."""
        # Given
        login_data = {
            "username": regular_user.username,
            "password": "wrong_password"
        }
        
        # When
        response = await async_client.post(
            "/api/v1/auth/login",
            data=login_data
        )
        
        # Then
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Incorrect username or password" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_login_with_nonexistent_user(self, async_client: AsyncClient):
        """Test login failure with non-existent user."""
        # Given
        login_data = {
            "username": "nonexistent_user",
            "password": "any_password"
        }
        
        # When
        response = await async_client.post(
            "/api/v1/auth/login",
            data=login_data
        )
        
        # Then
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_login_with_inactive_user(
        self, 
        async_client: AsyncClient,
        inactive_user
    ):
        """Test login failure with inactive user."""
        # Given
        login_data = {
            "username": inactive_user.username,
            "password": "testpassword123"
        }
        
        # When
        response = await async_client.post(
            "/api/v1/auth/login",
            data=login_data
        )
        
        # Then
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_login_with_missing_credentials(self, async_client: AsyncClient):
        """Test login failure with missing credentials."""
        # Given
        login_data = {
            "username": "testuser"
            # Missing password
        }
        
        # When
        response = await async_client.post(
            "/api/v1/auth/login",
            data=login_data
        )
        
        # Then
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_login_with_empty_credentials(self, async_client: AsyncClient):
        """Test login failure with empty credentials."""
        # Given
        login_data = {
            "username": "",
            "password": ""
        }
        
        # When
        response = await async_client.post(
            "/api/v1/auth/login",
            data=login_data
        )
        
        # Then
        assert response.status_code in [401, 422]  # Either auth failure or validation error


class TestProtectedEndpoints:
    """Test access to protected endpoints."""
    
    @pytest.mark.asyncio
    async def test_access_protected_endpoint_with_valid_token(
        self,
        async_client: AsyncClient,
        auth_headers_user
    ):
        """Test accessing protected endpoint with valid token."""
        # When
        response = await async_client.get(
            "/api/v1/users/me",
            headers=auth_headers_user
        )
        
        # Then
        assert response.status_code == 200
        data = response.json()
        assert "username" in data
        assert "email" in data
    
    @pytest.mark.asyncio
    async def test_access_protected_endpoint_without_token(
        self,
        async_client: AsyncClient
    ):
        """Test accessing protected endpoint without token."""
        # When
        response = await async_client.get("/api/v1/users/me")
        
        # Then
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Not authenticated" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_access_protected_endpoint_with_invalid_token(
        self,
        async_client: AsyncClient
    ):
        """Test accessing protected endpoint with invalid token."""
        # Given
        headers = {"Authorization": "Bearer invalid_token_here"}
        
        # When
        response = await async_client.get(
            "/api/v1/users/me",
            headers=headers
        )
        
        # Then
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_access_protected_endpoint_with_malformed_token(
        self,
        async_client: AsyncClient
    ):
        """Test accessing protected endpoint with malformed authorization header."""
        # Given
        headers = {"Authorization": "InvalidFormat token_here"}
        
        # When
        response = await async_client.get(
            "/api/v1/users/me",
            headers=headers
        )
        
        # Then
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data


class TestTokenRefresh:
    """Test token refresh functionality (if implemented)."""
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Token refresh not yet implemented")
    async def test_refresh_valid_token(
        self,
        async_client: AsyncClient,
        user_token
    ):
        """Test refreshing a valid token."""
        # Given
        headers = {"Authorization": f"Bearer {user_token}"}
        
        # When
        response = await async_client.post(
            "/api/v1/auth/refresh",
            headers=headers
        )
        
        # Then
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Token refresh not yet implemented")
    async def test_refresh_expired_token(self, async_client: AsyncClient):
        """Test refreshing an expired token."""
        # Given
        expired_token = "expired_token_here"
        headers = {"Authorization": f"Bearer {expired_token}"}
        
        # When
        response = await async_client.post(
            "/api/v1/auth/refresh",
            headers=headers
        )
        
        # Then
        assert response.status_code == 401


class TestRoleBasedAccess:
    """Test role-based access control."""
    
    @pytest.mark.asyncio
    async def test_admin_access_to_admin_endpoint(
        self,
        async_client: AsyncClient,
        auth_headers_admin
    ):
        """Test admin user accessing admin-only endpoint."""
        # When
        response = await async_client.get(
            "/api/v1/users/",
            headers=auth_headers_admin
        )
        
        # Then
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_user_denied_access_to_admin_endpoint(
        self,
        async_client: AsyncClient,
        auth_headers_user
    ):
        """Test regular user denied access to admin-only endpoint."""
        # When
        response = await async_client.get(
            "/api/v1/users/",
            headers=auth_headers_user
        )
        
        # Then
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        assert "Not enough permissions" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_user_access_to_own_data(
        self,
        async_client: AsyncClient,
        auth_headers_user
    ):
        """Test user can access their own data."""
        # When
        response = await async_client.get(
            "/api/v1/users/me",
            headers=auth_headers_user
        )
        
        # Then
        assert response.status_code == 200
        data = response.json()
        assert "username" in data
        assert "email" in data
        assert "role" in data
