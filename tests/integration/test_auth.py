"""Integration tests for authentication endpoints."""

import pytest

from app.models.user import User
from app.services.password import hash_password


class TestLoginPage:
    """Tests for login page."""

    def test_login_page_renders(self, client):
        """Should render login page."""
        response = client.get("/login")
        assert response.status_code == 200
        assert "Sign in" in response.text

    def test_login_page_has_form(self, client):
        """Should have login form."""
        response = client.get("/login")
        assert 'name="email"' in response.text
        assert 'name="password"' in response.text
        assert 'name="remember_me"' in response.text


class TestLogin:
    """Tests for login functionality."""

    def test_login_valid_credentials(self, client, db_session):
        """Should login with valid credentials."""
        # Create a user
        user = User(
            email="test@example.com",
            name="Test User",
            password_hash=hash_password("password123"),
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/login",
            data={"email": "test@example.com", "password": "password123"},
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert response.headers.get("location") == "/"
        assert "session_token" in response.cookies

    def test_login_invalid_password(self, client, db_session):
        """Should reject invalid password."""
        user = User(
            email="test@example.com",
            name="Test User",
            password_hash=hash_password("password123"),
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/login",
            data={"email": "test@example.com", "password": "wrongpassword"},
        )

        assert response.status_code == 400
        assert "Invalid email or password" in response.text

    def test_login_invalid_email(self, client):
        """Should reject non-existent email."""
        response = client.post(
            "/login",
            data={"email": "nonexistent@example.com", "password": "password123"},
        )

        assert response.status_code == 400
        assert "Invalid email or password" in response.text

    def test_login_inactive_user(self, client, db_session):
        """Should reject inactive user."""
        user = User(
            email="test@example.com",
            name="Test User",
            password_hash=hash_password("password123"),
            is_active=False,
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/login",
            data={"email": "test@example.com", "password": "password123"},
        )

        assert response.status_code == 400

    def test_login_remember_me(self, client, db_session):
        """Should set longer cookie with remember me."""
        user = User(
            email="test@example.com",
            name="Test User",
            password_hash=hash_password("password123"),
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/login",
            data={
                "email": "test@example.com",
                "password": "password123",
                "remember_me": "true",
            },
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert "session_token" in response.cookies

    def test_login_redirect_to_next(self, client, db_session):
        """Should redirect to next URL after login."""
        user = User(
            email="test@example.com",
            name="Test User",
            password_hash=hash_password("password123"),
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/login",
            data={
                "email": "test@example.com",
                "password": "password123",
                "next": "/projects",
            },
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert response.headers.get("location") == "/projects"


class TestLogout:
    """Tests for logout functionality."""

    def test_logout_clears_session(self, client, db_session):
        """Should clear session on logout."""
        # First login
        user = User(
            email="test@example.com",
            name="Test User",
            password_hash=hash_password("password123"),
        )
        db_session.add(user)
        db_session.commit()

        client.post(
            "/login",
            data={"email": "test@example.com", "password": "password123"},
        )

        # Then logout
        response = client.get("/logout", follow_redirects=False)

        assert response.status_code == 302
        assert response.headers.get("location") == "/login"

    def test_logout_without_session(self, client):
        """Should handle logout without session."""
        response = client.get("/logout", follow_redirects=False)
        assert response.status_code == 302


class TestProtectedRoutes:
    """Tests for protected route access."""

    def test_root_redirects_to_login(self, client):
        """Should redirect unauthenticated user to login."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers.get("location") == "/login"

    def test_root_shows_dashboard_when_authenticated(self, client, db_session):
        """Should show dashboard when authenticated."""
        user = User(
            email="test@example.com",
            name="Test User",
            password_hash=hash_password("password123"),
        )
        db_session.add(user)
        db_session.commit()

        # Login first
        client.post(
            "/login",
            data={"email": "test@example.com", "password": "password123"},
        )

        # Then access root
        response = client.get("/")
        assert response.status_code == 200
        assert "Welcome" in response.text

    def test_login_page_redirects_when_authenticated(self, client, db_session):
        """Should redirect authenticated user away from login page."""
        user = User(
            email="test@example.com",
            name="Test User",
            password_hash=hash_password("password123"),
        )
        db_session.add(user)
        db_session.commit()

        # Login first
        client.post(
            "/login",
            data={"email": "test@example.com", "password": "password123"},
        )

        # Try to access login page
        response = client.get("/login", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers.get("location") == "/"
