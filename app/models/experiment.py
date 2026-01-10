"""Experiment model."""

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.project import Project
    from app.models.replicate import Replicate
    from app.models.todo import Todo
    from app.models.note import Note


class ExperimentStatus(str, enum.Enum):
    """Experiment status options."""

    PLANNED = "planned"
    RUNNING = "running"
    ANALYZING = "analyzing"
    COMPLETE = "complete"
    ARCHIVED = "archived"


class Experiment(UUIDMixin, TimestampMixin, Base):
    """Experiment within a project."""

    __tablename__ = "experiments"
    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_experiment_project_name"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ExperimentStatus] = mapped_column(
        Enum(ExperimentStatus, name="experiment_status"),
        default=ExperimentStatus.PLANNED,
        nullable=False,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="experiments",
    )
    creator: Mapped["User"] = relationship(
        "User",
        back_populates="created_experiments",
        foreign_keys=[created_by],
    )
    replicates: Mapped[list["Replicate"]] = relationship(
        "Replicate",
        back_populates="experiment",
        cascade="all, delete-orphan",
    )
    todos: Mapped[list["Todo"]] = relationship(
        "Todo",
        back_populates="experiment",
    )
    notes: Mapped[list["Note"]] = relationship(
        "Note",
        back_populates="experiment",
    )

    def __repr__(self) -> str:
        return f"<Experiment {self.name}>"
