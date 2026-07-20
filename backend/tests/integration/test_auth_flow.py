"""
Integration tests for the complete authentication flow.

Tests the full lifecycle: register → login → get profile → refresh token → change password.
"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    """Create async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.fixture
def test_user():
    """Generate unique test user credentials."""
    unique = uuid.uuid4().hex[:8]
    return {
        "email": f"testuser_{unique}@example.com",
        "username": f"testuser_{unique}",
        "password": "SecureP@ss123!",
        "full_name": "Test User",
    }


@pytest.mark.asyncio
class TestAuthRegistration:
    """Tests for user registration."""

    async def test_register_success(self, client: AsyncClient, test_user: dict):
        """Should register a new user and return user data."""
        response = await client.post("/api/v1/auth/register", json=test_user)
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == test_user["email"]
        assert data["username"] == test_user["username"]
        assert "id" in data
        # Password should not be in response
        assert "password" not in data
        assert "hashed_password" not in data

    async def test_register_duplicate_email(self, client: AsyncClient, test_user: dict):
        """Should reject registration with existing email."""
        await client.post("/api/v1/auth/register", json=test_user)
        response = await client.post("/api/v1/auth/register", json=test_user)
        assert response.status_code == 409

    async def test_register_duplicate_username(self, client: AsyncClient, test_user: dict):
        """Should reject registration with existing username."""
        await client.post("/api/v1/auth/register", json=test_user)
        duplicate = test_user.copy()
        duplicate["email"] = f"other_{test_user['email']}"
        response = await client.post("/api/v1/auth/register", json=duplicate)
        assert response.status_code == 409


@pytest.mark.asyncio
class TestAuthLogin:
    """Tests for user login."""

    async def test_login_success(self, client: AsyncClient, test_user: dict):
        """Should return tokens on valid credentials."""
        await client.post("/api/v1/auth/register", json=test_user)
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "expires_in" in data
        assert data["expires_in"] > 0

    async def test_login_invalid_password(self, client: AsyncClient, test_user: dict):
        """Should reject login with wrong password."""
        await client.post("/api/v1/auth/register", json=test_user)
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user["email"],
                "password": "wrong_password",
            },
        )
        assert response.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Should reject login for non-existent user."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "any_password",
            },
        )
        assert response.status_code == 401


@pytest.mark.asyncio
class TestAuthProfile:
    """Tests for profile access."""

    async def test_get_profile_authenticated(self, client: AsyncClient, test_user: dict):
        """Should return user profile when authenticated."""
        await client.post("/api/v1/auth/register", json=test_user)
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"],
            },
        )
        token = login_resp.json()["access_token"]

        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user["email"]
        assert data["username"] == test_user["username"]

    async def test_get_profile_unauthenticated(self, client: AsyncClient):
        """Should reject profile access without token."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code in (401, 403)

    async def test_get_profile_invalid_token(self, client: AsyncClient):
        """Should reject profile access with invalid token."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token_here"},
        )
        assert response.status_code in (401, 403)


@pytest.mark.asyncio
class TestAuthRefreshToken:
    """Tests for token refresh flow."""

    async def test_refresh_token_success(self, client: AsyncClient, test_user: dict):
        """Should return new tokens with valid refresh token."""
        await client.post("/api/v1/auth/register", json=test_user)
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"],
            },
        )
        refresh_token = login_resp.json()["refresh_token"]

        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_with_invalid_token(self, client: AsyncClient):
        """Should reject refresh with invalid token."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_refresh_token"},
        )
        assert response.status_code == 401

    async def test_refresh_with_access_token(self, client: AsyncClient, test_user: dict):
        """Should reject refresh when using access token instead of refresh token."""
        await client.post("/api/v1/auth/register", json=test_user)
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"],
            },
        )
        access_token = login_resp.json()["access_token"]

        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token},
        )
        assert response.status_code == 401


@pytest.mark.asyncio
class TestAuthChangePassword:
    """Tests for password change flow."""

    async def test_change_password_success(self, client: AsyncClient, test_user: dict):
        """Should change password successfully."""
        await client.post("/api/v1/auth/register", json=test_user)
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"],
            },
        )
        token = login_resp.json()["access_token"]

        new_password = "NewSecureP@ss456!"
        response = await client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": test_user["password"],
                "new_password": new_password,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 204

        # Verify login with new password works
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user["email"],
                "password": new_password,
            },
        )
        assert login_resp.status_code == 200

    async def test_change_password_wrong_current(self, client: AsyncClient, test_user: dict):
        """Should reject password change with wrong current password."""
        await client.post("/api/v1/auth/register", json=test_user)
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"],
            },
        )
        token = login_resp.json()["access_token"]

        response = await client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "wrong_password",
                "new_password": "NewSecureP@ss456!",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 400

    async def test_change_password_unauthenticated(self, client: AsyncClient):
        """Should reject password change without authentication."""
        response = await client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "any",
                "new_password": "any",
            },
        )
        assert response.status_code in (401, 403)


@pytest.mark.asyncio
class TestFullAuthFlow:
    """End-to-end authentication flow test."""

    async def test_complete_auth_lifecycle(self, client: AsyncClient, test_user: dict):
        """Test the full auth lifecycle: register → login → profile → refresh → change password."""
        # 1. Register
        reg_resp = await client.post("/api/v1/auth/register", json=test_user)
        assert reg_resp.status_code == 201
        user_id = reg_resp.json()["id"]

        # 2. Login
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"],
            },
        )
        assert login_resp.status_code == 200
        tokens = login_resp.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        # 3. Get profile
        profile_resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert profile_resp.status_code == 200
        assert profile_resp.json()["id"] == user_id

        # 4. Refresh token
        refresh_resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_resp.status_code == 200
        new_access_token = refresh_resp.json()["access_token"]

        # 5. Use new token to access profile
        profile_resp2 = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {new_access_token}"},
        )
        assert profile_resp2.status_code == 200

        # 6. Change password
        new_password = "ChangedP@ssword789!"
        change_resp = await client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": test_user["password"],
                "new_password": new_password,
            },
            headers={"Authorization": f"Bearer {new_access_token}"},
        )
        assert change_resp.status_code == 204

        # 7. Login with new password
        final_login = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user["email"],
                "password": new_password,
            },
        )
        assert final_login.status_code == 200
