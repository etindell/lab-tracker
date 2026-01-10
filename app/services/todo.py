"""Todo service for managing todos."""

import uuid
from datetime import date
from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.experiment import Experiment
from app.models.project import Project
from app.models.replicate import Replicate
from app.models.todo import Todo, TodoPriority, TodoStatus
from app.models.user import User


class TodoService:
    """Service for todo management operations."""

    def __init__(self, db: Session):
        """Initialize with database session.

        Args:
            db: SQLAlchemy database session.
        """
        self.db = db

    def create_todo(
        self,
        title: str,
        created_by: User,
        description: Optional[str] = None,
        status: TodoStatus = TodoStatus.OPEN,
        priority: TodoPriority = TodoPriority.MEDIUM,
        due_date: Optional[date] = None,
        assigned_to: Optional[User] = None,
        project: Optional[Project] = None,
        experiment: Optional[Experiment] = None,
        replicate: Optional[Replicate] = None,
    ) -> Todo:
        """Create a new todo.

        Args:
            title: Todo title.
            created_by: User creating the todo.
            description: Todo description.
            status: Initial todo status.
            priority: Todo priority.
            due_date: Optional due date.
            assigned_to: User to assign todo to.
            project: Project to link todo to.
            experiment: Experiment to link todo to.
            replicate: Replicate to link todo to.

        Returns:
            Created Todo instance.
        """
        todo = Todo(
            title=title.strip(),
            description=description.strip() if description else None,
            status=status,
            priority=priority,
            due_date=due_date,
            created_by=created_by.id,
            assigned_to=assigned_to.id if assigned_to else None,
            project_id=project.id if project else None,
            experiment_id=experiment.id if experiment else None,
            replicate_id=replicate.id if replicate else None,
        )
        self.db.add(todo)
        self.db.commit()
        self.db.refresh(todo)
        return todo

    def get_by_id(self, todo_id: uuid.UUID) -> Optional[Todo]:
        """Get todo by ID.

        Args:
            todo_id: Todo UUID.

        Returns:
            Todo if found, None otherwise.
        """
        return self.db.get(Todo, todo_id)

    def list_todos(
        self,
        user: Optional[User] = None,
        status_filter: Optional[TodoStatus] = None,
        priority_filter: Optional[TodoPriority] = None,
        project: Optional[Project] = None,
        experiment: Optional[Experiment] = None,
        replicate: Optional[Replicate] = None,
        search: Optional[str] = None,
        include_done: bool = True,
    ) -> list[Todo]:
        """List todos with optional filtering.

        Args:
            user: Filter to todos created by or assigned to user.
            status_filter: Filter by specific status.
            priority_filter: Filter by specific priority.
            project: Filter by project.
            experiment: Filter by experiment.
            replicate: Filter by replicate.
            search: Search by title (case-insensitive).
            include_done: Include done todos.

        Returns:
            List of Todo instances.
        """
        stmt = select(Todo).order_by(Todo.created_at.desc())

        if user:
            stmt = stmt.where(
                or_(Todo.created_by == user.id, Todo.assigned_to == user.id)
            )

        if status_filter:
            stmt = stmt.where(Todo.status == status_filter)
        elif not include_done:
            stmt = stmt.where(Todo.status != TodoStatus.DONE)

        if priority_filter:
            stmt = stmt.where(Todo.priority == priority_filter)

        if project:
            stmt = stmt.where(Todo.project_id == project.id)

        if experiment:
            stmt = stmt.where(Todo.experiment_id == experiment.id)

        if replicate:
            stmt = stmt.where(Todo.replicate_id == replicate.id)

        if search:
            stmt = stmt.where(Todo.title.ilike(f"%{search}%"))

        return list(self.db.execute(stmt).scalars().all())

    def update_todo(
        self,
        todo: Todo,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[TodoStatus] = None,
        priority: Optional[TodoPriority] = None,
        due_date: Optional[date] = None,
        assigned_to: Optional[User] = None,
        project: Optional[Project] = None,
        experiment: Optional[Experiment] = None,
        replicate: Optional[Replicate] = None,
        clear_assignee: bool = False,
        clear_due_date: bool = False,
        clear_project: bool = False,
        clear_experiment: bool = False,
        clear_replicate: bool = False,
    ) -> Todo:
        """Update todo details.

        Args:
            todo: Todo instance to update.
            title: New title (optional).
            description: New description (optional).
            status: New status (optional).
            priority: New priority (optional).
            due_date: New due date (optional).
            assigned_to: New assignee (optional).
            project: New project link (optional).
            experiment: New experiment link (optional).
            replicate: New replicate link (optional).
            clear_assignee: Set to True to clear the assignee.
            clear_due_date: Set to True to clear the due date.
            clear_project: Set to True to clear the project link.
            clear_experiment: Set to True to clear the experiment link.
            clear_replicate: Set to True to clear the replicate link.

        Returns:
            Updated Todo instance.
        """
        if title is not None:
            todo.title = title.strip()

        if description is not None:
            todo.description = description.strip() if description else None

        if status is not None:
            todo.status = status

        if priority is not None:
            todo.priority = priority

        if due_date is not None:
            todo.due_date = due_date
        elif clear_due_date:
            todo.due_date = None

        if assigned_to is not None:
            todo.assigned_to = assigned_to.id
        elif clear_assignee:
            todo.assigned_to = None

        if project is not None:
            todo.project_id = project.id
        elif clear_project:
            todo.project_id = None

        if experiment is not None:
            todo.experiment_id = experiment.id
        elif clear_experiment:
            todo.experiment_id = None

        if replicate is not None:
            todo.replicate_id = replicate.id
        elif clear_replicate:
            todo.replicate_id = None

        self.db.commit()
        self.db.refresh(todo)
        return todo

    def change_status(self, todo: Todo, new_status: TodoStatus) -> Todo:
        """Change todo status (inline update).

        Args:
            todo: Todo to update.
            new_status: New status.

        Returns:
            Updated Todo instance.
        """
        todo.status = new_status
        self.db.commit()
        self.db.refresh(todo)
        return todo

    def delete_todo(self, todo: Todo) -> None:
        """Delete a todo.

        Args:
            todo: Todo to delete.
        """
        self.db.delete(todo)
        self.db.commit()
