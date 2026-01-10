"""Project model."""

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


class ProjectStatus(str, enum.Enum):
    """Project status options."""

    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETE = "complete"
    ARCHIVED = "archived"


class Project(UUIDMixin, TimestampMixin, Base):
    """Research project model."""

    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, name="project_status"),
        default=ProjectStatus.ACTIVE,
        nullable=False,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    # Relationships
    creator: Mapped["User"] = relationship(
        "User",
        back_populates="created_projects",
        foreign_keys=[created_by],
    )
    experiments: Mapped[list["Experiment"]] = relationship(
        "Experiment",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    todos: Mapped[list["Todo"]] = relationship(
        "Todo",
        back_populates="project",
    )

    def __repr__(self) -> str:
        return f"<Project {self.name}>"
