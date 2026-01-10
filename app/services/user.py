"""User service for managing user accounts."""

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.password import hash_password, verify_password


class UserService:
    """Service for user management operations."""

    def __init__(self, db: Session):
        """Initialize with database session.

        Args:
            db: SQLAlchemy database session.
        """
        self.db = db

    def create_user(
        self,
        email: str,
        name: str,
        password: str,
        is_admin: bool = False,
    ) -> User:
        """Create a new user account.

        Args:
            email: User's email address (unique).
            name: User's display name.
            password: Plain text password (will be hashed).
            is_admin: Whether user has admin privileges.

        Returns:
            Created User instance.

        Raises:
            ValueError: If email already exists.
        """
        # Check for existing email
        existing = self.get_by_email(email)
        if existing:
            raise ValueError(f"User with email {email} already exists")

        user = User(
            email=email.lower().strip(),
            name=name.strip(),
            password_hash=hash_password(password),
            is_admin=is_admin,
            is_active=True,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Get user by ID.

        Args:
            user_id: User's UUID.

        Returns:
            User if found, None otherwise.
        """
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address.

        Args:
            email: User's email address.

        Returns:
            User if found, None otherwise.
        """
        stmt = select(User).where(User.email == email.lower().strip())
        return self.db.execute(stmt).scalar_one_or_none()

    def authenticate(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password.

        Args:
            email: User's email address.
            password: Plain text password.

        Returns:
            User if authentication successful, None otherwise.
        """
        user = self.get_by_email(email)
        if not user:
            return None
        if not user.is_active:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    def change_password(
        self,
        user: User,
        current_password: str,
        new_password: str,
    ) -> bool:
        """Change user's password.

        Args:
            user: User instance.
            current_password: Current plain text password.
            new_password: New plain text password.

        Returns:
            True if password changed, False if current password incorrect.
        """
        if not verify_password(current_password, user.password_hash):
            return False

        user.password_hash = hash_password(new_password)
        self.db.commit()
        return True

    def reset_password(self, user: User, new_password: str) -> None:
        """Reset user's password (admin operation).

        Args:
            user: User instance.
            new_password: New plain text password.
        """
        user.password_hash = hash_password(new_password)
        self.db.commit()

    def deactivate_user(self, user: User) -> None:
        """Deactivate a user account (soft delete).

        Args:
            user: User instance to deactivate.
        """
        user.is_active = False
        self.db.commit()

    def reactivate_user(self, user: User) -> None:
        """Reactivate a deactivated user account.

        Args:
            user: User instance to reactivate.
        """
        user.is_active = True
        self.db.commit()

    def list_users(self, include_inactive: bool = False) -> list[User]:
        """List all users.

        Args:
            include_inactive: Whether to include deactivated users.

        Returns:
            List of User instances.
        """
        stmt = select(User).order_by(User.name)
        if not include_inactive:
            stmt = stmt.where(User.is_active == True)  # noqa: E712
        return list(self.db.execute(stmt).scalars().all())

    def update_user(
        self,
        user: User,
        name: Optional[str] = None,
        email: Optional[str] = None,
        is_admin: Optional[bool] = None,
    ) -> User:
        """Update user details.

        Args:
            user: User instance to update.
            name: New name (optional).
            email: New email (optional).
            is_admin: New admin status (optional).

        Returns:
            Updated User instance.

        Raises:
            ValueError: If new email already exists.
        """
        if email is not None and email.lower().strip() != user.email:
            existing = self.get_by_email(email)
            if existing:
                raise ValueError(f"User with email {email} already exists")
            user.email = email.lower().strip()

        if name is not None:
            user.name = name.strip()

        if is_admin is not None:
            user.is_admin = is_admin

        self.db.commit()
        self.db.refresh(user)
        return user
