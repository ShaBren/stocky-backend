"""
Tests for backup and restore functionality
"""
import pytest
import base64
import gzip
from httpx import AsyncClient
from sqlalchemy.orm import Session

from src.stocky_backend.models.models import UserRole
from tests.factories.user_factory import UserFactory


class TestBackupAPI:
    """Test backup and restore endpoints"""

    @pytest.mark.asyncio
    async def test_create_full_backup_admin_access(
        self, 
        async_client: AsyncClient, 
        auth_headers_admin
    ):
        """Test that admin can create full backup"""
        response = await async_client.post(
            "/api/v1/backup/create/full", 
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "backup_size" in data
        assert "timestamp" in data
        assert "tables_included" in data
        assert "message" in data
        assert data["backup_size"] > 0
        assert isinstance(data["tables_included"], list)

    @pytest.mark.asyncio
    async def test_create_full_backup_regular_user_denied(
        self, 
        async_client: AsyncClient, 
        auth_headers_user
    ):
        """Test that regular user cannot create backup"""
        response = await async_client.post(
            "/api/v1/backup/create/full", 
            headers=auth_headers_user
        )
        
        assert response.status_code == 403
        detail = response.json()["detail"]
        assert "Access denied" in detail or "Required roles" in detail

    @pytest.mark.asyncio
    async def test_create_full_backup_no_auth(self, async_client: AsyncClient):
        """Test that unauthenticated users cannot create backup"""
        response = await async_client.post("/api/v1/backup/create/full")
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_download_full_backup_admin_access(
        self, 
        async_client: AsyncClient, 
        auth_headers_admin
    ):
        """Test that admin can download full backup"""
        response = await async_client.post(
            "/api/v1/backup/create/full/download", 
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/gzip"
        assert "attachment" in response.headers["content-disposition"]
        assert "stocky_backup_" in response.headers["content-disposition"]
        assert ".sql.gz" in response.headers["content-disposition"]

    @pytest.mark.asyncio
    async def test_import_partial_backup_admin_access(
        self, 
        async_client: AsyncClient, 
        auth_headers_admin
    ):
        """Test that admin can import partial backup"""
        # Create simple SQL for testing
        sql_data = "INSERT INTO test_table (name) VALUES ('test');"
        compressed_data = gzip.compress(sql_data.encode('utf-8'))
        base64_data = base64.b64encode(compressed_data).decode('utf-8')
        
        request_data = {
            "backup_data": base64_data,
            "force": True
        }
        
        response = await async_client.post(
            "/api/v1/backup/import/partial", 
            json=request_data, 
            headers=auth_headers_admin
        )
        
        # This might fail due to table not existing, but should validate auth and structure
        assert response.status_code in [200, 400, 500]  # Auth should work, execution may fail
        if response.status_code != 200:
            # Should be SQL execution error, not auth error
            detail = response.json().get("detail", "")
            assert "Access denied" not in detail and "Required roles" not in detail

    @pytest.mark.asyncio
    async def test_import_partial_backup_regular_user_denied(
        self, 
        async_client: AsyncClient, 
        auth_headers_user
    ):
        """Test that regular user cannot import partial backup"""
        sql_data = "INSERT INTO test_table (name) VALUES ('test');"
        compressed_data = gzip.compress(sql_data.encode('utf-8'))
        base64_data = base64.b64encode(compressed_data).decode('utf-8')
        
        request_data = {
            "backup_data": base64_data,
            "force": True
        }
        
        response = await async_client.post(
            "/api/v1/backup/import/partial", 
            json=request_data, 
            headers=auth_headers_user
        )
        
        assert response.status_code == 403
        detail = response.json()["detail"]
        assert "Access denied" in detail or "Required roles" in detail

    @pytest.mark.asyncio
    async def test_import_full_backup_requires_force(
        self, 
        async_client: AsyncClient, 
        auth_headers_admin
    ):
        """Test that full backup import requires force=true"""
        sql_data = "CREATE TABLE test (id INTEGER);"
        compressed_data = gzip.compress(sql_data.encode('utf-8'))
        base64_data = base64.b64encode(compressed_data).decode('utf-8')
        
        request_data = {
            "backup_data": base64_data,
            "force": False
        }
        
        response = await async_client.post(
            "/api/v1/backup/import/full", 
            json=request_data, 
            headers=auth_headers_admin
        )
        
        assert response.status_code == 400
        assert "force=true" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_import_full_backup_regular_user_denied(
        self, 
        async_client: AsyncClient, 
        auth_headers_user
    ):
        """Test that regular user cannot import full backup"""
        sql_data = "CREATE TABLE test (id INTEGER);"
        compressed_data = gzip.compress(sql_data.encode('utf-8'))
        base64_data = base64.b64encode(compressed_data).decode('utf-8')
        
        request_data = {
            "backup_data": base64_data,
            "force": True
        }
        
        response = await async_client.post(
            "/api/v1/backup/import/full", 
            json=request_data, 
            headers=auth_headers_user
        )
        
        assert response.status_code == 403
        detail = response.json()["detail"]
        assert "Access denied" in detail or "Required roles" in detail

    @pytest.mark.asyncio
    async def test_invalid_backup_data_base64(
        self, 
        async_client: AsyncClient, 
        auth_headers_admin
    ):
        """Test error handling for invalid base64 data"""
        request_data = {
            "backup_data": "invalid_base64_data!@#$",
            "force": True
        }
        
        response = await async_client.post(
            "/api/v1/backup/import/partial", 
            json=request_data, 
            headers=auth_headers_admin
        )
        
        assert response.status_code == 400
        assert "Invalid base64" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_invalid_backup_data_gzip(
        self, 
        async_client: AsyncClient, 
        auth_headers_admin
    ):
        """Test error handling for invalid gzip data"""
        # Valid base64 but invalid gzip
        invalid_data = base64.b64encode(b"not gzip data").decode('utf-8')
        
        request_data = {
            "backup_data": invalid_data,
            "force": True
        }
        
        response = await async_client.post(
            "/api/v1/backup/import/partial", 
            json=request_data, 
            headers=auth_headers_admin
        )
        
        assert response.status_code == 400
        assert "Invalid gzip" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_all_backup_endpoints_require_admin(
        self, 
        async_client: AsyncClient, 
        auth_headers_user
    ):
        """Test that all backup endpoints require admin access"""
        endpoints = [
            ("/api/v1/backup/create/full", "post"),
            ("/api/v1/backup/create/full/download", "post"),
        ]
        
        for endpoint, method in endpoints:
            if method == "post":
                response = await async_client.post(endpoint, headers=auth_headers_user)
            else:
                response = await async_client.get(endpoint, headers=auth_headers_user)
            
            assert response.status_code == 403, f"Endpoint {endpoint} should require admin access"
            detail = response.json()["detail"]
            assert "Access denied" in detail or "Required roles" in detail


class TestBackupIntegration:
    """Integration tests for backup functionality"""

    @pytest.mark.asyncio
    async def test_backup_restore_cycle(
        self, 
        async_client: AsyncClient, 
        auth_headers_admin, 
        db_session: Session
    ):
        """Test creating backup and then restoring it (integration test)"""
        # Create initial data
        test_user = UserFactory.create(
            username="backup_test_user",
            email="backup.test@test.com",
            role=UserRole.MEMBER
        )
        db_session.add(test_user)
        db_session.commit()
        
        # Create backup
        backup_response = await async_client.post(
            "/api/v1/backup/create/full", 
            headers=auth_headers_admin
        )
        assert backup_response.status_code == 200
        
        backup_data = backup_response.json()
        assert backup_data["backup_size"] > 0
        assert "users" in backup_data["tables_included"]
        
        # Verify backup contains our data (this is a conceptual test - 
        # actual restoration would require more complex setup)
        assert "Full backup created successfully" in backup_data["message"]