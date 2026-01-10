"""Activity service for logging user actions."""

import uuid
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.activity import ActivityLog
from app.models.user import User


class ActivityService:
    """Service for activity logging operations."""

    def __init__(self, db: Session):
        """Initialize with database session.

        Args:
            db: SQLAlchemy database session.
        """
        self.db = db

    def log_activity(
        self,
        user: User,
        action: str,
        entity_type: str,
        entity_id: uuid.UUID,
        metadata: Optional[dict[str, Any]] = None,
    ) -> ActivityLog:
        """Log a user activity.

        Args:
            user: User performing the action.
            action: Action type (create, update, delete, etc.).
            entity_type: Type of entity (project, experiment, etc.).
            entity_id: UUID of the entity.
            metadata: Optional metadata about the action.

        Returns:
            Created ActivityLog instance.
        """
        activity = ActivityLog(
            user_id=user.id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata_json=metadata,
        )
        self.db.add(activity)
        self.db.commit()
        self.db.refresh(activity)
        return activity

    def list_activities(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[uuid.UUID] = None,
        user: Optional[User] = None,
        limit: int = 50,
    ) -> list[ActivityLog]:
        """List activities with optional filtering.

        Args:
            entity_type: Filter by entity type.
            entity_id: Filter by entity ID.
            user: Filter by user.
            limit: Maximum number of activities to return.

        Returns:
            List of ActivityLog instances.
        """
        stmt = select(ActivityLog).order_by(ActivityLog.created_at.desc())

        if entity_type:
            stmt = stmt.where(ActivityLog.entity_type == entity_type)

        if entity_id:
            stmt = stmt.where(ActivityLog.entity_id == entity_id)

        if user:
            stmt = stmt.where(ActivityLog.user_id == user.id)

        stmt = stmt.limit(limit)

        return list(self.db.execute(stmt).scalars().all())

    def get_recent_activities(
        self,
        limit: int = 20,
        entity_type: Optional[str] = None,
    ) -> list[ActivityLog]:
        """Get recent activities across the system.

        Args:
            limit: Maximum number of activities to return.
            entity_type: Optional filter by entity type.

        Returns:
            List of ActivityLog instances.
        """
        stmt = select(ActivityLog).order_by(ActivityLog.created_at.desc())

        if entity_type:
            stmt = stmt.where(ActivityLog.entity_type == entity_type)

        stmt = stmt.limit(limit)

        return list(self.db.execute(stmt).scalars().all())
