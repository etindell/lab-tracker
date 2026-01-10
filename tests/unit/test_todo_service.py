"""Unit tests for todo service."""

import pytest
from datetime import date, timedelta

from app.models.user import User
from app.models.project import Project
from app.models.experiment import Experiment
from app.models.todo import Todo, TodoStatus, TodoPriority
from app.services.todo import TodoService
from app.services.password import hash_password


class TestTodoServiceCreate:
    """Tests for todo creation."""

    def test_create_todo(self, db_session):
        """Should create a new todo."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        service = TodoService(db_session)
        todo = service.create_todo(
            title="Test Todo",
            created_by=user,
            description="A test todo",
        )

        assert todo.id is not None
        assert todo.title == "Test Todo"
        assert todo.description == "A test todo"
        assert todo.status == TodoStatus.OPEN
        assert todo.priority == TodoPriority.MEDIUM
        assert todo.created_by == user.id

    def test_create_todo_with_priority(self, db_session):
        """Should create todo with specified priority."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        service = TodoService(db_session)
        todo = service.create_todo(
            title="High Priority Todo",
            created_by=user,
            priority=TodoPriority.HIGH,
        )

        assert todo.priority == TodoPriority.HIGH

    def test_create_todo_with_due_date(self, db_session):
        """Should create todo with due date."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        service = TodoService(db_session)
        due = date.today() + timedelta(days=7)
        todo = service.create_todo(
            title="Due Todo",
            created_by=user,
            due_date=due,
        )

        assert todo.due_date == due

    def test_create_todo_with_assignment(self, db_session):
        """Should create todo with assignee."""
        owner = User(
            email="owner@example.com",
            name="Owner",
            password_hash=hash_password("password"),
        )
        assignee = User(
            email="assignee@example.com",
            name="Assignee",
            password_hash=hash_password("password"),
        )
        db_session.add_all([owner, assignee])
        db_session.commit()

        service = TodoService(db_session)
        todo = service.create_todo(
            title="Assigned Todo",
            created_by=owner,
            assigned_to=assignee,
        )

        assert todo.assigned_to == assignee.id

    def test_create_todo_linked_to_project(self, db_session):
        """Should create todo linked to project."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        project = Project(name="Test Project", created_by=user.id)
        db_session.add(project)
        db_session.commit()

        service = TodoService(db_session)
        todo = service.create_todo(
            title="Project Todo",
            created_by=user,
            project=project,
        )

        assert todo.project_id == project.id

    def test_create_todo_linked_to_experiment(self, db_session):
        """Should create todo linked to experiment."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        project = Project(name="Test Project", created_by=user.id)
        db_session.add(project)
        db_session.commit()

        experiment = Experiment(
            name="Test Experiment",
            project_id=project.id,
            created_by=user.id,
        )
        db_session.add(experiment)
        db_session.commit()

        service = TodoService(db_session)
        todo = service.create_todo(
            title="Experiment Todo",
            created_by=user,
            experiment=experiment,
        )

        assert todo.experiment_id == experiment.id


class TestTodoServiceList:
    """Tests for listing todos."""

    def test_list_todos_by_user(self, db_session):
        """Should list todos created by or assigned to user."""
        user1 = User(
            email="user1@example.com",
            name="User 1",
            password_hash=hash_password("password"),
        )
        user2 = User(
            email="user2@example.com",
            name="User 2",
            password_hash=hash_password("password"),
        )
        db_session.add_all([user1, user2])
        db_session.commit()

        service = TodoService(db_session)
        # User1 creates a todo
        service.create_todo(title="Created by User1", created_by=user1)
        # User2 creates a todo assigned to User1
        service.create_todo(
            title="Assigned to User1", created_by=user2, assigned_to=user1
        )
        # User2 creates their own todo
        service.create_todo(title="User2's todo", created_by=user2)

        todos = service.list_todos(user=user1)
        assert len(todos) == 2
        titles = [t.title for t in todos]
        assert "Created by User1" in titles
        assert "Assigned to User1" in titles

    def test_list_todos_all(self, db_session):
        """Should list all todos when no user specified."""
        user = User(
            email="user@example.com",
            name="User",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        service = TodoService(db_session)
        service.create_todo(title="Todo 1", created_by=user)
        service.create_todo(title="Todo 2", created_by=user)
        service.create_todo(title="Todo 3", created_by=user)

        todos = service.list_todos()
        assert len(todos) == 3

    def test_list_todos_filter_by_status(self, db_session):
        """Should filter by status."""
        user = User(
            email="user@example.com",
            name="User",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        service = TodoService(db_session)
        service.create_todo(title="Open Todo", created_by=user)
        todo2 = service.create_todo(title="Done Todo", created_by=user)
        service.update_todo(todo2, status=TodoStatus.DONE)

        todos = service.list_todos(status_filter=TodoStatus.OPEN)
        assert len(todos) == 1
        assert todos[0].title == "Open Todo"

    def test_list_todos_filter_by_priority(self, db_session):
        """Should filter by priority."""
        user = User(
            email="user@example.com",
            name="User",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        service = TodoService(db_session)
        service.create_todo(
            title="High Priority", created_by=user, priority=TodoPriority.HIGH
        )
        service.create_todo(
            title="Low Priority", created_by=user, priority=TodoPriority.LOW
        )

        todos = service.list_todos(priority_filter=TodoPriority.HIGH)
        assert len(todos) == 1
        assert todos[0].title == "High Priority"

    def test_list_todos_filter_by_project(self, db_session):
        """Should filter by project."""
        user = User(
            email="user@example.com",
            name="User",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        project = Project(name="Test Project", created_by=user.id)
        db_session.add(project)
        db_session.commit()

        service = TodoService(db_session)
        service.create_todo(title="Project Todo", created_by=user, project=project)
        service.create_todo(title="Unlinked Todo", created_by=user)

        todos = service.list_todos(project=project)
        assert len(todos) == 1
        assert todos[0].title == "Project Todo"

    def test_list_todos_search(self, db_session):
        """Should search by title."""
        user = User(
            email="user@example.com",
            name="User",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        service = TodoService(db_session)
        service.create_todo(title="Alpha Task", created_by=user)
        service.create_todo(title="Beta Work", created_by=user)

        todos = service.list_todos(search="alpha")
        assert len(todos) == 1
        assert todos[0].title == "Alpha Task"


class TestTodoServiceUpdate:
    """Tests for updating todos."""

    def test_update_todo_title(self, db_session):
        """Should update todo title."""
        user = User(
            email="user@example.com",
            name="User",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        service = TodoService(db_session)
        todo = service.create_todo(title="Old Title", created_by=user)

        updated = service.update_todo(todo, title="New Title")
        assert updated.title == "New Title"

    def test_update_todo_status(self, db_session):
        """Should update todo status."""
        user = User(
            email="user@example.com",
            name="User",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        service = TodoService(db_session)
        todo = service.create_todo(title="Test", created_by=user)

        updated = service.update_todo(todo, status=TodoStatus.IN_PROGRESS)
        assert updated.status == TodoStatus.IN_PROGRESS

    def test_update_todo_assignment(self, db_session):
        """Should update todo assignment."""
        user = User(
            email="user@example.com",
            name="User",
            password_hash=hash_password("password"),
        )
        assignee = User(
            email="assignee@example.com",
            name="Assignee",
            password_hash=hash_password("password"),
        )
        db_session.add_all([user, assignee])
        db_session.commit()

        service = TodoService(db_session)
        todo = service.create_todo(title="Test", created_by=user)

        updated = service.update_todo(todo, assigned_to=assignee)
        assert updated.assigned_to == assignee.id


class TestTodoServiceChangeStatus:
    """Tests for changing todo status."""

    def test_change_status(self, db_session):
        """Should change todo status."""
        user = User(
            email="user@example.com",
            name="User",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        service = TodoService(db_session)
        todo = service.create_todo(title="Test", created_by=user)

        updated = service.change_status(todo, TodoStatus.DONE)
        assert updated.status == TodoStatus.DONE


class TestTodoServiceDelete:
    """Tests for deleting todos."""

    def test_delete_todo(self, db_session):
        """Should delete a todo."""
        user = User(
            email="user@example.com",
            name="User",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        service = TodoService(db_session)
        todo = service.create_todo(title="Test", created_by=user)
        todo_id = todo.id

        service.delete_todo(todo)

        deleted = service.get_by_id(todo_id)
        assert deleted is None
