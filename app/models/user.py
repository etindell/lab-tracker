"""User model."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.experiment import Experiment
    from app.models.replicate import Replicate
    from app.models.todo import Todo
    from app.models.note import Note
    from app.models.activity import ActivityLog


class User(UUIDMixin, TimestampMixin, Base):
    """User account model."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    created_projects: Mapped[list["Project"]] = relationship(
        "Project",
        back_populates="creator",
        foreign_keys="Project.created_by",
    )
    created_experiments: Mapped[list["Experiment"]] = relationship(
        "Experiment",
        back_populates="creator",
        foreign_keys="Experiment.created_by",
    )
    performed_replicates: Mapped[list["Replicate"]] = relationship(
        "Replicate",
        back_populates="performer",
        foreign_keys="Replicate.performed_by",
    )
    assigned_todos: Mapped[list["Todo"]] = relationship(
        "Todo",
        back_populates="assignee",
        foreign_keys="Todo.assigned_to",
    )
    created_todos: Mapped[list["Todo"]] = relationship(
        "Todo",
        back_populates="creator",
        foreign_keys="Todo.created_by",
    )
    notes: Mapped[list["Note"]] = relationship(
        "Note",
        back_populates="author",
    )
    activities: Mapped[list["ActivityLog"]] = relationship(
        "ActivityLog",
        back_populates="user",
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"
