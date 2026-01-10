"""FastAPI dependencies for authentication."""

from typing import Annotated, Optional

from fastapi import Cookie, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.session import SessionService
from app.database import get_db
from app.models.user import User


SESSION_COOKIE_NAME = "session_token"


def get_session_token(
    session_token: Annotated[Optional[str], Cookie()] = None,
) -> Optional[str]:
    """Extract session token from cookie.

    Args:
        session_token: Session token from cookie.

    Returns:
        Session token or None if not present.
    """
    return session_token


def get_current_user_optional(
    db: Annotated[Session, Depends(get_db)],
    token: Annotated[Optional[str], Depends(get_session_token)],
) -> Optional[User]:
    """Get current user if authenticated.

    Args:
        db: Database session.
        token: Session token.

    Returns:
        User if authenticated, None otherwise.
    """
    if not token:
        return None

    session_service = SessionService(db)
    return session_service.get_user_by_token(token)


def get_current_user(
    user: Annotated[Optional[User], Depends(get_current_user_optional)],
) -> User:
    """Get current authenticated user.

    Args:
        user: User from optional dependency.

    Returns:
        Authenticated user.

    Raises:
        HTTPException: 401 if not authenticated.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Cookie"},
        )
    return user


def require_admin(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Require current user to be an admin.

    Args:
        user: Authenticated user.

    Returns:
        Admin user.

    Raises:
        HTTPException: 403 if not admin.
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user
