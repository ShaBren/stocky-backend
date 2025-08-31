"""End-to-end workflow tests for user management."""

import pytest
from httpx import AsyncClient


class TestUserManagementWorkflow:
    """Test complete user management workflows."""
    
    @pytest.mark.asyncio
    async def test_complete_user_registration_login_workflow(
        self,
        async_client: AsyncClient,
        admin_user,
        auth_headers_admin
    ):
        """Test complete workflow: admin creates user, user logs in, accesses data."""
        
        # Step 1: Admin creates a new user
        new_user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpassword123",
            "role": "MEMBER"
        }
        
        create_response = await async_client.post(
            "/api/v1/users/",
            json=new_user_data,
            headers=auth_headers_admin
        )
        
        assert create_response.status_code == 201
        created_user = create_response.json()
        assert created_user["username"] == "newuser"
        assert created_user["email"] == "newuser@example.com"
        assert created_user["is_active"] is True
        user_id = created_user["id"]
        
        # Step 2: New user logs in
        login_data = {
            "username": "newuser",
            "password": "newpassword123"
        }
        
        login_response = await async_client.post(
            "/api/v1/auth/login",
            data=login_data
        )
        
        assert login_response.status_code == 200
        login_result = login_response.json()
        assert "access_token" in login_result
        user_token = login_result["access_token"]
        
        # Step 3: User accesses their own data
        user_headers = {"Authorization": f"Bearer {user_token}"}
        
        profile_response = await async_client.get(
            "/api/v1/users/me",
            headers=user_headers
        )
        
        assert profile_response.status_code == 200
        profile_data = profile_response.json()
        assert profile_data["username"] == "newuser"
        assert profile_data["email"] == "newuser@example.com"
        assert profile_data["id"] == user_id
        
        # Step 4: User updates their profile
        update_data = {
            "email": "updated@example.com"
        }
        
        update_response = await async_client.put(
            "/api/v1/users/me",
            json=update_data,
            headers=user_headers
        )
        
        assert update_response.status_code == 200
        updated_profile = update_response.json()
        assert updated_profile["email"] == "updated@example.com"
        
        # Step 5: Verify changes persist
        final_profile_response = await async_client.get(
            "/api/v1/users/me",
            headers=user_headers
        )
        
        assert final_profile_response.status_code == 200
        final_profile = final_profile_response.json()
        assert final_profile["email"] == "updated@example.com"
    
    @pytest.mark.asyncio
    async def test_user_deactivation_workflow(
        self,
        async_client: AsyncClient,
        admin_user,
        auth_headers_admin
    ):
        """Test complete workflow: create user, deactivate, verify access denied."""
        
        # Step 1: Admin creates a new user
        new_user_data = {
            "username": "tempuser",
            "email": "temp@example.com",
            "password": "temppassword123",
            "role": "MEMBER"
        }
        
        create_response = await async_client.post(
            "/api/v1/users/",
            json=new_user_data,
            headers=auth_headers_admin
        )
        
        assert create_response.status_code == 201
        created_user = create_response.json()
        user_id = created_user["id"]
        
        # Step 2: User logs in successfully
        login_data = {
            "username": "tempuser",
            "password": "temppassword123"
        }
        
        login_response = await async_client.post(
            "/api/v1/auth/login",
            data=login_data
        )
        
        assert login_response.status_code == 200
        user_token = login_response.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}
        
        # Step 3: User can access their data
        profile_response = await async_client.get(
            "/api/v1/users/me",
            headers=user_headers
        )
        assert profile_response.status_code == 200
        
        # Step 4: Admin deactivates the user
        deactivate_data = {"is_active": False}
        
        deactivate_response = await async_client.put(
            f"/api/v1/users/{user_id}",
            json=deactivate_data,
            headers=auth_headers_admin
        )
        
        assert deactivate_response.status_code == 200
        deactivated_user = deactivate_response.json()
        assert deactivated_user["is_active"] is False
        
        # Step 5: User can no longer log in
        new_login_response = await async_client.post(
            "/api/v1/auth/login",
            data=login_data
        )
        
        assert new_login_response.status_code == 401
        
        # Step 6: Existing token should be invalidated (if token validation checks user status)
        # Note: This depends on implementation - some systems invalidate tokens, others don't
        profile_response_after = await async_client.get(
            "/api/v1/users/me",
            headers=user_headers
        )
        # This might be 401 or 403 depending on implementation
        assert profile_response_after.status_code in [401, 403]
    
    @pytest.mark.asyncio
    async def test_admin_user_management_workflow(
        self,
        async_client: AsyncClient,
        admin_user,
        auth_headers_admin
    ):
        """Test admin workflow: create multiple users, list, update, delete."""
        
        # Step 1: Create multiple users
        users_to_create = [
            {
                "username": f"user{i}",
                "email": f"user{i}@example.com",
                "password": f"password{i}",
                "role": "MEMBER"
            }
            for i in range(1, 4)
        ]
        
        created_user_ids = []
        for user_data in users_to_create:
            response = await async_client.post(
                "/api/v1/users/",
                json=user_data,
                headers=auth_headers_admin
            )
            assert response.status_code == 201
            created_user_ids.append(response.json()["id"])
        
        # Step 2: Admin lists all users
        list_response = await async_client.get(
            "/api/v1/users/",
            headers=auth_headers_admin
        )
        
        assert list_response.status_code == 200
        all_users = list_response.json()
        assert len(all_users) >= 3  # At least the 3 we created (plus admin)
        
        # Verify our created users are in the list
        usernames = [user["username"] for user in all_users]
        for i in range(1, 4):
            assert f"user{i}" in usernames
        
        # Step 3: Admin updates a user
        user_to_update_id = created_user_ids[0]
        update_data = {
            "role": "ADMIN"
        }
        
        update_response = await async_client.put(
            f"/api/v1/users/{user_to_update_id}",
            json=update_data,
            headers=auth_headers_admin
        )
        
        assert update_response.status_code == 200
        updated_user = update_response.json()
        assert updated_user["role"] == "ADMIN"
        
        # Step 4: Admin deletes a user
        user_to_delete_id = created_user_ids[1]
        
        delete_response = await async_client.delete(
            f"/api/v1/users/{user_to_delete_id}",
            headers=auth_headers_admin
        )
        
        assert delete_response.status_code == 200
        
        # Step 5: Verify user is deleted
        get_deleted_response = await async_client.get(
            f"/api/v1/users/{user_to_delete_id}",
            headers=auth_headers_admin
        )
        
        assert get_deleted_response.status_code == 404
        
        # Step 6: Verify remaining users still exist
        for user_id in [created_user_ids[0], created_user_ids[2]]:
            get_response = await async_client.get(
                f"/api/v1/users/{user_id}",
                headers=auth_headers_admin
            )
            assert get_response.status_code == 200


class TestPermissionWorkflows:
    """Test permission-based workflows."""
    
    @pytest.mark.asyncio
    async def test_user_permission_escalation_attempt(
        self,
        async_client: AsyncClient,
        auth_headers_user
    ):
        """Test that regular users cannot perform admin actions."""
        
        # Step 1: User tries to create another user (admin only)
        new_user_data = {
            "username": "unauthorizeduser",
            "email": "unauthorized@example.com",
            "password": "password123",
            "role": "MEMBER"
        }
        
        create_response = await async_client.post(
            "/api/v1/users/",
            json=new_user_data,
            headers=auth_headers_user
        )
        
        assert create_response.status_code == 403
        
        # Step 2: User tries to list all users (admin only)
        list_response = await async_client.get(
            "/api/v1/users/",
            headers=auth_headers_user
        )
        
        assert list_response.status_code == 403
        
        # Step 3: User tries to access another user's data
        # Note: This assumes we have another user with ID 999
        other_user_response = await async_client.get(
            "/api/v1/users/999",
            headers=auth_headers_user
        )
        
        assert other_user_response.status_code in [403, 404]  # Forbidden or not found
    
    @pytest.mark.asyncio
    async def test_user_can_only_modify_own_data(
        self,
        async_client: AsyncClient,
        regular_user,
        auth_headers_user
    ):
        """Test that users can only modify their own data."""
        
        # Step 1: User can access their own data
        own_data_response = await async_client.get(
            "/api/v1/users/me",
            headers=auth_headers_user
        )
        
        assert own_data_response.status_code == 200
        own_data = own_data_response.json()
        assert own_data["username"] == regular_user.username
        
        # Step 2: User can update their own data
        update_data = {
        }
        
        update_response = await async_client.put(
            "/api/v1/users/me",
            json=update_data,
            headers=auth_headers_user
        )
        
        assert update_response.status_code == 200
        updated_data = update_response.json()
        
        # Step 3: User cannot update their own role (security restriction)
        role_update_data = {
            "role": "ADMIN"
        }
        
        role_update_response = await async_client.put(
            "/api/v1/users/me",
            json=role_update_data,
            headers=auth_headers_user
        )
        
        # This should either be forbidden or the role change should be ignored
        if role_update_response.status_code == 200:
            # If the request succeeds, verify role wasn't actually changed
            profile_response = await async_client.get(
                "/api/v1/users/me",
                headers=auth_headers_user
            )
            profile_data = profile_response.json()
            assert profile_data["role"] != "ADMIN"  # Role should not have changed
        else:
            assert role_update_response.status_code == 403
