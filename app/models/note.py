"""Note model."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.experiment import Experiment
    from app.models.replicate import Replicate


class Note(UUIDMixin, TimestampMixin, Base):
    """Note attached to experiment or replicate."""

    __tablename__ = "notes"
    __table_args__ = (
        CheckConstraint(
            "experiment_id IS NOT NULL OR replicate_id IS NOT NULL",
            name="ck_note_has_parent",
        ),
    )

    content: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    experiment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    replicate_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("replicates.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Relationships
    author: Mapped["User"] = relationship(
        "User",
        back_populates="notes",
    )
    experiment: Mapped["Experiment | None"] = relationship(
        "Experiment",
        back_populates="notes",
    )
    replicate: Mapped["Replicate | None"] = relationship(
        "Replicate",
        back_populates="notes",
    )

    def __repr__(self) -> str:
        return f"<Note by {self.author_id}>"
