"""Replicate service for managing replicates within experiments."""

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.experiment import Experiment
from app.models.replicate import Replicate, ReplicateStatus
from app.models.user import User


class ReplicateService:
    """Service for replicate management operations."""

    def __init__(self, db: Session):
        """Initialize with database session.

        Args:
            db: SQLAlchemy database session.
        """
        self.db = db

    def create_replicate(
        self,
        experiment: Experiment,
        name: str,
        summary: Optional[str] = None,
        status: ReplicateStatus = ReplicateStatus.PLANNED,
        performed_by: Optional[User] = None,
        results_link: Optional[str] = None,
        notes_text: Optional[str] = None,
    ) -> Replicate:
        """Create a new replicate within an experiment.

        Args:
            experiment: Experiment to create replicate in.
            name: Replicate name.
            summary: Replicate summary.
            status: Initial replicate status.
            performed_by: User performing the replicate.
            results_link: Link to results.
            notes_text: Additional notes.

        Returns:
            Created Replicate instance.
        """
        replicate = Replicate(
            experiment_id=experiment.id,
            name=name.strip(),
            summary=summary.strip() if summary else None,
            status=status,
            performed_by=performed_by.id if performed_by else None,
            results_link=results_link.strip() if results_link else None,
            notes_text=notes_text.strip() if notes_text else None,
        )
        self.db.add(replicate)
        self.db.commit()
        self.db.refresh(replicate)
        return replicate

    def get_by_id(self, replicate_id: uuid.UUID) -> Optional[Replicate]:
        """Get replicate by ID.

        Args:
            replicate_id: Replicate UUID.

        Returns:
            Replicate if found, None otherwise.
        """
        return self.db.get(Replicate, replicate_id)

    def list_replicates(
        self,
        experiment: Experiment,
        status_filter: Optional[ReplicateStatus] = None,
        search: Optional[str] = None,
    ) -> list[Replicate]:
        """List replicates for an experiment with optional filtering.

        Args:
            experiment: Experiment to list replicates for.
            status_filter: Filter by specific status.
            search: Search by name (case-insensitive).

        Returns:
            List of Replicate instances.
        """
        stmt = (
            select(Replicate)
            .where(Replicate.experiment_id == experiment.id)
            .order_by(Replicate.created_at.asc())
        )

        if status_filter:
            stmt = stmt.where(Replicate.status == status_filter)

        if search:
            stmt = stmt.where(Replicate.name.ilike(f"%{search}%"))

        return list(self.db.execute(stmt).scalars().all())

    def update_replicate(
        self,
        replicate: Replicate,
        name: Optional[str] = None,
        summary: Optional[str] = None,
        status: Optional[ReplicateStatus] = None,
        performed_by: Optional[User] = None,
        results_link: Optional[str] = None,
        notes_text: Optional[str] = None,
        clear_performer: bool = False,
    ) -> Replicate:
        """Update replicate details.

        Args:
            replicate: Replicate instance to update.
            name: New name (optional).
            summary: New summary (optional).
            status: New status (optional).
            performed_by: New performer (optional).
            results_link: New results link (optional).
            notes_text: New notes text (optional).
            clear_performer: Set to True to clear the performer.

        Returns:
            Updated Replicate instance.
        """
        if name is not None:
            replicate.name = name.strip()

        if summary is not None:
            replicate.summary = summary.strip() if summary else None

        if status is not None:
            replicate.status = status

        if performed_by is not None:
            replicate.performed_by = performed_by.id
        elif clear_performer:
            replicate.performed_by = None

        if results_link is not None:
            replicate.results_link = results_link.strip() if results_link else None

        if notes_text is not None:
            replicate.notes_text = notes_text.strip() if notes_text else None

        self.db.commit()
        self.db.refresh(replicate)
        return replicate

    def change_status(
        self, replicate: Replicate, new_status: ReplicateStatus
    ) -> Replicate:
        """Change replicate status (inline update).

        Args:
            replicate: Replicate to update.
            new_status: New status.

        Returns:
            Updated Replicate instance.
        """
        replicate.status = new_status
        self.db.commit()
        self.db.refresh(replicate)
        return replicate

    def delete_replicate(self, replicate: Replicate) -> None:
        """Delete a replicate.

        Args:
            replicate: Replicate to delete.
        """
        self.db.delete(replicate)
        self.db.commit()
