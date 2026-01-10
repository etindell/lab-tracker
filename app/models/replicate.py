"""Replicate (run) model."""

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.experiment import Experiment
    from app.models.todo import Todo
    from app.models.note import Note


class ReplicateStatus(str, enum.Enum):
    """Replicate status options."""

    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"


class Replicate(UUIDMixin, TimestampMixin, Base):
    """Replicate (run) within an experiment."""

    __tablename__ = "replicates"

    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    performed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    status: Mapped[ReplicateStatus] = mapped_column(
        Enum(ReplicateStatus, name="replicate_status"),
        default=ReplicateStatus.PLANNED,
        nullable=False,
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    results_link: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    notes_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    experiment: Mapped["Experiment"] = relationship(
        "Experiment",
        back_populates="replicates",
    )
    performer: Mapped["User | None"] = relationship(
        "User",
        back_populates="performed_replicates",
        foreign_keys=[performed_by],
    )
    todos: Mapped[list["Todo"]] = relationship(
        "Todo",
        back_populates="replicate",
    )
    notes: Mapped[list["Note"]] = relationship(
        "Note",
        back_populates="replicate",
    )

    def __repr__(self) -> str:
        return f"<Replicate {self.name}>"
