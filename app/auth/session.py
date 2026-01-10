"""Server-side session management."""

import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session as DBSession

from app.config import get_settings
from app.models.session import Session
from app.models.user import User


settings = get_settings()


class SessionService:
    """Service for managing server-side sessions."""

    def __init__(self, db: DBSession):
        """Initialize with database session.

        Args:
            db: SQLAlchemy database session.
        """
        self.db = db

    def create_session(
        self,
        user: User,
        remember_me: bool = False,
    ) -> str:
        """Create a new session for a user.

        Args:
            user: User to create session for.
            remember_me: Whether to extend session duration.

        Returns:
            Session token string.
        """
        # Generate secure token
        token = secrets.token_urlsafe(32)

        # Calculate expiry
        if remember_me:
            expire_seconds = settings.session_expire_remember_seconds
        else:
            expire_seconds = settings.session_expire_seconds

        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expire_seconds)

        # Create session
        session = Session(
            user_id=user.id,
            session_token=token,
            expires_at=expires_at,
        )
        self.db.add(session)
        self.db.commit()

        return token

    def get_user_by_token(self, token: str) -> Optional[User]:
        """Get user associated with a session token.

        Args:
            token: Session token to look up.

        Returns:
            User if valid session exists, None otherwise.
        """
        stmt = (
            select(Session)
            .where(Session.session_token == token)
            .where(Session.expires_at > datetime.now(timezone.utc))
        )
        session = self.db.execute(stmt).scalar_one_or_none()

        if not session:
            return None

        # Get user and check if active
        user = self.db.get(User, session.user_id)
        if not user or not user.is_active:
            # Delete invalid session
            self.db.delete(session)
            self.db.commit()
            return None

        return user

    def delete_session(self, token: str) -> None:
        """Delete a session (logout).

        Args:
            token: Session token to delete.
        """
        stmt = delete(Session).where(Session.session_token == token)
        self.db.execute(stmt)
        self.db.commit()

    def delete_user_sessions(self, user_id: uuid.UUID) -> None:
        """Delete all sessions for a user.

        Args:
            user_id: User ID to delete sessions for.
        """
        stmt = delete(Session).where(Session.user_id == user_id)
        self.db.execute(stmt)
        self.db.commit()

    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions from database.

        Returns:
            Number of sessions deleted.
        """
        stmt = delete(Session).where(Session.expires_at <= datetime.now(timezone.utc))
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount

    def extend_session(self, token: str, remember_me: bool = False) -> bool:
        """Extend a session's expiry time.

        Args:
            token: Session token to extend.
            remember_me: Whether to use extended duration.

        Returns:
            True if session was extended, False if not found.
        """
        stmt = select(Session).where(Session.session_token == token)
        session = self.db.execute(stmt).scalar_one_or_none()

        if not session:
            return False

        if remember_me:
            expire_seconds = settings.session_expire_remember_seconds
        else:
            expire_seconds = settings.session_expire_seconds

        session.expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=expire_seconds
        )
        self.db.commit()
        return True
