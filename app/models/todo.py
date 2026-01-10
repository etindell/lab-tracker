"""Todo model."""

import enum
import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.project import Project
    from app.models.experiment import Experiment
    from app.models.replicate import Replicate


class TodoStatus(str, enum.Enum):
    """Todo status options."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"


class TodoPriority(str, enum.Enum):
    """Todo priority options."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Todo(UUIDMixin, TimestampMixin, Base):
    """Todo item model."""

    __tablename__ = "todos"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[TodoStatus] = mapped_column(
        Enum(TodoStatus, name="todo_status"),
        default=TodoStatus.OPEN,
        nullable=False,
        index=True,
    )
    priority: Mapped[TodoPriority] = mapped_column(
        Enum(TodoPriority, name="todo_priority"),
        default=TodoPriority.MEDIUM,
        nullable=False,
    )
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Foreign keys for assignment and linking
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    experiment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="SET NULL"),
        nullable=True,
    )
    replicate_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("replicates.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    assignee: Mapped["User | None"] = relationship(
        "User",
        back_populates="assigned_todos",
        foreign_keys=[assigned_to],
    )
    creator: Mapped["User"] = relationship(
        "User",
        back_populates="created_todos",
        foreign_keys=[created_by],
    )
    project: Mapped["Project | None"] = relationship(
        "Project",
        back_populates="todos",
    )
    experiment: Mapped["Experiment | None"] = relationship(
        "Experiment",
        back_populates="todos",
    )
    replicate: Mapped["Replicate | None"] = relationship(
        "Replicate",
        back_populates="todos",
    )

    def __repr__(self) -> str:
        return f"<Todo {self.title}>"
