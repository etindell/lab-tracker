"""Integration tests for admin routes."""

import pytest

from app.models.user import User
from app.services.password import hash_password


class TestAdminAccess:
    """Tests for admin access control."""

    def test_admin_page_requires_auth(self, client):
        """Should require authentication for admin pages."""
        response = client.get("/admin/users", follow_redirects=False)
        # Should redirect to login (302) or return 401
        assert response.status_code in [302, 401]

    def test_admin_page_requires_admin_role(self, client, db_session):
        """Should require admin role for admin pages."""
        # Create a regular user
        user = User(
            email="user@example.com",
            name="Regular User",
            password_hash=hash_password("password123"),
            is_admin=False,
        )
        db_session.add(user)
        db_session.commit()

        # Login as regular user
        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password123"},
        )

        # Try to access admin page
        response = client.get("/admin/users")
        assert response.status_code == 403

    def test_admin_page_accessible_by_admin(self, client, db_session):
        """Should allow admin to access admin pages."""
        # Create an admin user
        admin = User(
            email="admin@example.com",
            name="Admin User",
            password_hash=hash_password("adminpass"),
            is_admin=True,
        )
        db_session.add(admin)
        db_session.commit()

        # Login as admin
        client.post(
            "/login",
            data={"email": "admin@example.com", "password": "adminpass"},
        )

        # Access admin page
        response = client.get("/admin/users")
        assert response.status_code == 200
        assert "User Management" in response.text


class TestUserList:
    """Tests for user list page."""

    def test_user_list_shows_users(self, client, db_session):
        """Should show list of users."""
        # Create admin
        admin = User(
            email="admin@example.com",
            name="Admin User",
            password_hash=hash_password("adminpass"),
            is_admin=True,
        )
        user = User(
            email="user@example.com",
            name="Test User",
            password_hash=hash_password("password"),
        )
        db_session.add_all([admin, user])
        db_session.commit()

        # Login as admin
        client.post(
            "/login",
            data={"email": "admin@example.com", "password": "adminpass"},
        )

        response = client.get("/admin/users")
        assert response.status_code == 200
        assert "Admin User" in response.text
        assert "Test User" in response.text

    def test_user_list_hides_inactive_by_default(self, client, db_session):
        """Should hide inactive users by default."""
        admin = User(
            email="admin@example.com",
            name="Admin User",
            password_hash=hash_password("adminpass"),
            is_admin=True,
        )
        inactive_user = User(
            email="inactive@example.com",
            name="Inactive User",
            password_hash=hash_password("password"),
            is_active=False,
        )
        db_session.add_all([admin, inactive_user])
        db_session.commit()

        client.post(
            "/login",
            data={"email": "admin@example.com", "password": "adminpass"},
        )

        response = client.get("/admin/users")
        assert response.status_code == 200
        assert "Inactive User" not in response.text

    def test_user_list_shows_inactive_when_requested(self, client, db_session):
        """Should show inactive users when requested."""
        admin = User(
            email="admin@example.com",
            name="Admin User",
            password_hash=hash_password("adminpass"),
            is_admin=True,
        )
        inactive_user = User(
            email="inactive@example.com",
            name="Inactive User",
            password_hash=hash_password("password"),
            is_active=False,
        )
        db_session.add_all([admin, inactive_user])
        db_session.commit()

        client.post(
            "/login",
            data={"email": "admin@example.com", "password": "adminpass"},
        )

        response = client.get("/admin/users?show_inactive=true")
        assert response.status_code == 200
        assert "Inactive User" in response.text


class TestCreateUser:
    """Tests for creating users."""

    def test_create_user_form_renders(self, client, db_session):
        """Should render create user form."""
        admin = User(
            email="admin@example.com",
            name="Admin User",
            password_hash=hash_password("adminpass"),
            is_admin=True,
        )
        db_session.add(admin)
        db_session.commit()

        client.post(
            "/login",
            data={"email": "admin@example.com", "password": "adminpass"},
        )

        response = client.get("/admin/users/new")
        assert response.status_code == 200
        assert "Create New User" in response.text

    def test_create_user_success(self, client, db_session):
        """Should create a new user successfully."""
        admin = User(
            email="admin@example.com",
            name="Admin User",
            password_hash=hash_password("adminpass"),
            is_admin=True,
        )
        db_session.add(admin)
        db_session.commit()

        client.post(
            "/login",
            data={"email": "admin@example.com", "password": "adminpass"},
        )

        response = client.post(
            "/admin/users/new",
            data={
                "email": "newuser@example.com",
                "name": "New User",
            },
        )

        assert response.status_code == 200
        assert "User Created Successfully" in response.text
        assert "newuser@example.com" in response.text
        # Should show temporary password
        assert "Temporary Password" in response.text

    def test_create_user_duplicate_email(self, client, db_session):
        """Should reject duplicate email."""
        admin = User(
            email="admin@example.com",
            name="Admin User",
            password_hash=hash_password("adminpass"),
            is_admin=True,
        )
        existing = User(
            email="existing@example.com",
            name="Existing User",
            password_hash=hash_password("password"),
        )
        db_session.add_all([admin, existing])
        db_session.commit()

        client.post(
            "/login",
            data={"email": "admin@example.com", "password": "adminpass"},
        )

        response = client.post(
            "/admin/users/new",
            data={
                "email": "existing@example.com",
                "name": "New User",
            },
        )

        assert response.status_code == 400
        assert "already exists" in response.text


class TestDeactivateUser:
    """Tests for deactivating users."""

    def test_deactivate_user(self, client, db_session):
        """Should deactivate a user."""
        admin = User(
            email="admin@example.com",
            name="Admin User",
            password_hash=hash_password("adminpass"),
            is_admin=True,
        )
        target = User(
            email="target@example.com",
            name="Target User",
            password_hash=hash_password("password"),
        )
        db_session.add_all([admin, target])
        db_session.commit()
        target_id = target.id

        client.post(
            "/login",
            data={"email": "admin@example.com", "password": "adminpass"},
        )

        response = client.post(
            f"/admin/users/{target_id}/deactivate",
            follow_redirects=False,
        )

        assert response.status_code == 302

        # Verify user is deactivated
        db_session.refresh(target)
        assert target.is_active is False

    def test_cannot_deactivate_self(self, client, db_session):
        """Should not allow admin to deactivate themselves."""
        admin = User(
            email="admin@example.com",
            name="Admin User",
            password_hash=hash_password("adminpass"),
            is_admin=True,
        )
        db_session.add(admin)
        db_session.commit()
        admin_id = admin.id

        client.post(
            "/login",
            data={"email": "admin@example.com", "password": "adminpass"},
        )

        client.post(f"/admin/users/{admin_id}/deactivate")

        # Admin should still be active
        db_session.refresh(admin)
        assert admin.is_active is True


class TestReactivateUser:
    """Tests for reactivating users."""

    def test_reactivate_user(self, client, db_session):
        """Should reactivate a user."""
        admin = User(
            email="admin@example.com",
            name="Admin User",
            password_hash=hash_password("adminpass"),
            is_admin=True,
        )
        target = User(
            email="target@example.com",
            name="Target User",
            password_hash=hash_password("password"),
            is_active=False,
        )
        db_session.add_all([admin, target])
        db_session.commit()
        target_id = target.id

        client.post(
            "/login",
            data={"email": "admin@example.com", "password": "adminpass"},
        )

        response = client.post(
            f"/admin/users/{target_id}/reactivate",
            follow_redirects=False,
        )

        assert response.status_code == 302

        # Verify user is reactivated
        db_session.refresh(target)
        assert target.is_active is True


class TestResetPassword:
    """Tests for resetting passwords."""

    def test_reset_password(self, client, db_session):
        """Should reset user password."""
        admin = User(
            email="admin@example.com",
            name="Admin User",
            password_hash=hash_password("adminpass"),
            is_admin=True,
        )
        target = User(
            email="target@example.com",
            name="Target User",
            password_hash=hash_password("oldpassword"),
        )
        db_session.add_all([admin, target])
        db_session.commit()
        target_id = target.id

        client.post(
            "/login",
            data={"email": "admin@example.com", "password": "adminpass"},
        )

        response = client.post(f"/admin/users/{target_id}/reset-password")

        assert response.status_code == 200
        assert "Password Reset Successfully" in response.text
        assert "New Temporary Password" in response.text
