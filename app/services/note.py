"""Note service for managing notes."""

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.experiment import Experiment
from app.models.note import Note
from app.models.replicate import Replicate
from app.models.user import User


class NoteService:
    """Service for note management operations."""

    def __init__(self, db: Session):
        """Initialize with database session.

        Args:
            db: SQLAlchemy database session.
        """
        self.db = db

    def create_note(
        self,
        content: str,
        author: User,
        experiment: Optional[Experiment] = None,
        replicate: Optional[Replicate] = None,
    ) -> Note:
        """Create a new note.

        Args:
            content: Note content (Markdown supported).
            author: User creating the note.
            experiment: Experiment to attach note to.
            replicate: Replicate to attach note to.

        Returns:
            Created Note instance.

        Raises:
            ValueError: If neither experiment nor replicate provided.
        """
        if experiment is None and replicate is None:
            raise ValueError("Note must be attached to an experiment or replicate")

        note = Note(
            content=content,
            author_id=author.id,
            experiment_id=experiment.id if experiment else None,
            replicate_id=replicate.id if replicate else None,
        )
        self.db.add(note)
        self.db.commit()
        self.db.refresh(note)
        return note

    def get_by_id(self, note_id: uuid.UUID) -> Optional[Note]:
        """Get note by ID.

        Args:
            note_id: Note UUID.

        Returns:
            Note if found, None otherwise.
        """
        return self.db.get(Note, note_id)

    def list_notes(
        self,
        experiment: Optional[Experiment] = None,
        replicate: Optional[Replicate] = None,
    ) -> list[Note]:
        """List notes for an experiment or replicate.

        Args:
            experiment: Filter by experiment.
            replicate: Filter by replicate.

        Returns:
            List of Note instances.
        """
        stmt = select(Note).order_by(Note.created_at.desc())

        if experiment:
            stmt = stmt.where(Note.experiment_id == experiment.id)

        if replicate:
            stmt = stmt.where(Note.replicate_id == replicate.id)

        return list(self.db.execute(stmt).scalars().all())

    def update_note(
        self,
        note: Note,
        content: Optional[str] = None,
    ) -> Note:
        """Update note content.

        Args:
            note: Note instance to update.
            content: New content (optional).

        Returns:
            Updated Note instance.
        """
        if content is not None:
            note.content = content

        self.db.commit()
        self.db.refresh(note)
        return note

    def delete_note(self, note: Note) -> None:
        """Delete a note.

        Args:
            note: Note to delete.
        """
        self.db.delete(note)
        self.db.commit()
