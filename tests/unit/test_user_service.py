"""Unit tests for user service."""

import pytest

from app.models.user import User
from app.services.user import UserService
from app.services.password import verify_password


class TestUserServiceCreate:
    """Tests for user creation."""

    def test_create_user(self, db_session):
        """Should create a new user."""
        service = UserService(db_session)
        user = service.create_user(
            email="test@example.com",
            name="Test User",
            password="password123",
        )

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.is_active is True
        assert user.is_admin is False

    def test_create_user_hashes_password(self, db_session):
        """Should hash the password."""
        service = UserService(db_session)
        user = service.create_user(
            email="test@example.com",
            name="Test User",
            password="password123",
        )

        assert user.password_hash != "password123"
        assert verify_password("password123", user.password_hash)

    def test_create_admin_user(self, db_session):
        """Should create an admin user."""
        service = UserService(db_session)
        user = service.create_user(
            email="admin@example.com",
            name="Admin User",
            password="adminpass",
            is_admin=True,
        )

        assert user.is_admin is True

    def test_create_user_normalizes_email(self, db_session):
        """Should normalize email to lowercase."""
        service = UserService(db_session)
        user = service.create_user(
            email="  TEST@EXAMPLE.COM  ",
            name="Test User",
            password="password123",
        )

        assert user.email == "test@example.com"

    def test_create_user_trims_name(self, db_session):
        """Should trim whitespace from name."""
        service = UserService(db_session)
        user = service.create_user(
            email="test@example.com",
            name="  Test User  ",
            password="password123",
        )

        assert user.name == "Test User"

    def test_create_user_duplicate_email_raises(self, db_session):
        """Should raise error for duplicate email."""
        service = UserService(db_session)
        service.create_user(
            email="test@example.com",
            name="Test User",
            password="password123",
        )

        with pytest.raises(ValueError, match="already exists"):
            service.create_user(
                email="test@example.com",
                name="Another User",
                password="password456",
            )


class TestUserServiceAuthenticate:
    """Tests for user authentication."""

    def test_authenticate_valid_credentials(self, db_session):
        """Should authenticate with valid credentials."""
        service = UserService(db_session)
        service.create_user(
            email="test@example.com",
            name="Test User",
            password="password123",
        )

        user = service.authenticate("test@example.com", "password123")
        assert user is not None
        assert user.email == "test@example.com"

    def test_authenticate_invalid_password(self, db_session):
        """Should return None for invalid password."""
        service = UserService(db_session)
        service.create_user(
            email="test@example.com",
            name="Test User",
            password="password123",
        )

        user = service.authenticate("test@example.com", "wrongpassword")
        assert user is None

    def test_authenticate_invalid_email(self, db_session):
        """Should return None for non-existent email."""
        service = UserService(db_session)

        user = service.authenticate("nonexistent@example.com", "password123")
        assert user is None

    def test_authenticate_inactive_user(self, db_session):
        """Should return None for inactive user."""
        service = UserService(db_session)
        user = service.create_user(
            email="test@example.com",
            name="Test User",
            password="password123",
        )
        service.deactivate_user(user)

        result = service.authenticate("test@example.com", "password123")
        assert result is None

    def test_authenticate_normalizes_email(self, db_session):
        """Should normalize email during authentication."""
        service = UserService(db_session)
        service.create_user(
            email="test@example.com",
            name="Test User",
            password="password123",
        )

        user = service.authenticate("  TEST@EXAMPLE.COM  ", "password123")
        assert user is not None


class TestUserServicePasswordManagement:
    """Tests for password management."""

    def test_change_password_valid(self, db_session):
        """Should change password with valid current password."""
        service = UserService(db_session)
        user = service.create_user(
            email="test@example.com",
            name="Test User",
            password="oldpassword",
        )

        result = service.change_password(user, "oldpassword", "newpassword")
        assert result is True
        assert verify_password("newpassword", user.password_hash)

    def test_change_password_invalid_current(self, db_session):
        """Should reject change with invalid current password."""
        service = UserService(db_session)
        user = service.create_user(
            email="test@example.com",
            name="Test User",
            password="oldpassword",
        )

        result = service.change_password(user, "wrongpassword", "newpassword")
        assert result is False
        # Password should not have changed
        assert verify_password("oldpassword", user.password_hash)

    def test_reset_password(self, db_session):
        """Should reset password without current password."""
        service = UserService(db_session)
        user = service.create_user(
            email="test@example.com",
            name="Test User",
            password="oldpassword",
        )

        service.reset_password(user, "newpassword")
        assert verify_password("newpassword", user.password_hash)


class TestUserServiceDeactivation:
    """Tests for user deactivation."""

    def test_deactivate_user(self, db_session):
        """Should deactivate a user."""
        service = UserService(db_session)
        user = service.create_user(
            email="test@example.com",
            name="Test User",
            password="password123",
        )

        service.deactivate_user(user)
        assert user.is_active is False

    def test_reactivate_user(self, db_session):
        """Should reactivate a deactivated user."""
        service = UserService(db_session)
        user = service.create_user(
            email="test@example.com",
            name="Test User",
            password="password123",
        )
        service.deactivate_user(user)

        service.reactivate_user(user)
        assert user.is_active is True


class TestUserServiceList:
    """Tests for listing users."""

    def test_list_users(self, db_session):
        """Should list all active users."""
        service = UserService(db_session)
        service.create_user(
            email="user1@example.com",
            name="User One",
            password="password",
        )
        service.create_user(
            email="user2@example.com",
            name="User Two",
            password="password",
        )

        users = service.list_users()
        assert len(users) == 2

    def test_list_users_excludes_inactive(self, db_session):
        """Should exclude inactive users by default."""
        service = UserService(db_session)
        active_user = service.create_user(
            email="active@example.com",
            name="Active User",
            password="password",
        )
        inactive_user = service.create_user(
            email="inactive@example.com",
            name="Inactive User",
            password="password",
        )
        service.deactivate_user(inactive_user)

        users = service.list_users()
        assert len(users) == 1
        assert users[0].email == "active@example.com"

    def test_list_users_include_inactive(self, db_session):
        """Should include inactive users when requested."""
        service = UserService(db_session)
        service.create_user(
            email="active@example.com",
            name="Active User",
            password="password",
        )
        inactive_user = service.create_user(
            email="inactive@example.com",
            name="Inactive User",
            password="password",
        )
        service.deactivate_user(inactive_user)

        users = service.list_users(include_inactive=True)
        assert len(users) == 2


class TestUserServiceUpdate:
    """Tests for updating user details."""

    def test_update_user_name(self, db_session):
        """Should update user name."""
        service = UserService(db_session)
        user = service.create_user(
            email="test@example.com",
            name="Old Name",
            password="password",
        )

        updated = service.update_user(user, name="New Name")
        assert updated.name == "New Name"

    def test_update_user_email(self, db_session):
        """Should update user email."""
        service = UserService(db_session)
        user = service.create_user(
            email="old@example.com",
            name="Test User",
            password="password",
        )

        updated = service.update_user(user, email="new@example.com")
        assert updated.email == "new@example.com"

    def test_update_user_email_duplicate_raises(self, db_session):
        """Should raise error for duplicate email."""
        service = UserService(db_session)
        service.create_user(
            email="existing@example.com",
            name="Existing User",
            password="password",
        )
        user = service.create_user(
            email="test@example.com",
            name="Test User",
            password="password",
        )

        with pytest.raises(ValueError, match="already exists"):
            service.update_user(user, email="existing@example.com")

    def test_update_user_admin_status(self, db_session):
        """Should update admin status."""
        service = UserService(db_session)
        user = service.create_user(
            email="test@example.com",
            name="Test User",
            password="password",
        )
        assert user.is_admin is False

        updated = service.update_user(user, is_admin=True)
        assert updated.is_admin is True
