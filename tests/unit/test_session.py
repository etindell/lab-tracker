"""Unit tests for session service."""

from datetime import datetime, timedelta, timezone

import pytest

from app.auth.session import SessionService
from app.models.user import User
from app.models.session import Session
from app.services.password import hash_password


class TestSessionServiceCreate:
    """Tests for session creation."""

    def test_create_session(self, db_session):
        """Should create a session for a user."""
        user = User(
            email="test@example.com",
            name="Test User",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        service = SessionService(db_session)
        token = service.create_session(user)

        assert token is not None
        assert len(token) > 20  # Secure token should be long

    def test_create_session_stores_in_db(self, db_session):
        """Should store session in database."""
        user = User(
            email="test@example.com",
            name="Test User",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        service = SessionService(db_session)
        token = service.create_session(user)

        # Query the session
        session = db_session.query(Session).filter_by(session_token=token).first()
        assert session is not None
        assert session.user_id == user.id

    def test_create_session_remember_me_extends_expiry(self, db_session):
        """Should extend expiry when remember_me is True."""
        user = User(
            email="test@example.com",
            name="Test User",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        service = SessionService(db_session)
        token_normal = service.create_session(user, remember_me=False)
        token_remember = service.create_session(user, remember_me=True)

        session_normal = db_session.query(Session).filter_by(session_token=token_normal).first()
        session_remember = db_session.query(Session).filter_by(session_token=token_remember).first()

        # Remember me session should expire later
        assert session_remember.expires_at > session_normal.expires_at


class TestSessionServiceGetUser:
    """Tests for getting user by session token."""

    def test_get_user_by_valid_token(self, db_session):
        """Should return user for valid token."""
        user = User(
            email="test@example.com",
            name="Test User",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        service = SessionService(db_session)
        token = service.create_session(user)

        found_user = service.get_user_by_token(token)
        assert found_user is not None
        assert found_user.id == user.id

    def test_get_user_by_invalid_token(self, db_session):
        """Should return None for invalid token."""
        service = SessionService(db_session)
        found_user = service.get_user_by_token("invalid-token")
        assert found_user is None

    def test_get_user_by_expired_token(self, db_session):
        """Should return None for expired token."""
        user = User(
            email="test@example.com",
            name="Test User",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        # Create session and manually expire it
        service = SessionService(db_session)
        token = service.create_session(user)

        session = db_session.query(Session).filter_by(session_token=token).first()
        session.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        db_session.commit()

        found_user = service.get_user_by_token(token)
        assert found_user is None

    def test_get_user_inactive_user(self, db_session):
        """Should return None for inactive user."""
        user = User(
            email="test@example.com",
            name="Test User",
            password_hash=hash_password("password"),
            is_active=False,
        )
        db_session.add(user)
        db_session.commit()

        # Manually create a session for inactive user
        session = Session(
            user_id=user.id,
            session_token="test-token",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db_session.add(session)
        db_session.commit()

        service = SessionService(db_session)
        found_user = service.get_user_by_token("test-token")
        assert found_user is None


class TestSessionServiceDelete:
    """Tests for session deletion."""

    def test_delete_session(self, db_session):
        """Should delete a session."""
        user = User(
            email="test@example.com",
            name="Test User",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        service = SessionService(db_session)
        token = service.create_session(user)

        service.delete_session(token)

        # Session should be gone
        session = db_session.query(Session).filter_by(session_token=token).first()
        assert session is None

    def test_delete_user_sessions(self, db_session):
        """Should delete all sessions for a user."""
        user = User(
            email="test@example.com",
            name="Test User",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        service = SessionService(db_session)
        # Create multiple sessions
        service.create_session(user)
        service.create_session(user)
        service.create_session(user)

        service.delete_user_sessions(user.id)

        # All sessions should be gone
        sessions = db_session.query(Session).filter_by(user_id=user.id).all()
        assert len(sessions) == 0


class TestSessionServiceCleanup:
    """Tests for session cleanup."""

    def test_cleanup_expired_sessions(self, db_session):
        """Should remove expired sessions."""
        user = User(
            email="test@example.com",
            name="Test User",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        # Create expired and valid sessions
        expired_session = Session(
            user_id=user.id,
            session_token="expired-token",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        valid_session = Session(
            user_id=user.id,
            session_token="valid-token",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db_session.add_all([expired_session, valid_session])
        db_session.commit()

        service = SessionService(db_session)
        deleted_count = service.cleanup_expired_sessions()

        assert deleted_count == 1
        # Valid session should still exist
        session = db_session.query(Session).filter_by(session_token="valid-token").first()
        assert session is not None
