"""Integration tests for todo routes."""

import pytest
from datetime import date, timedelta

from app.models.user import User
from app.models.project import Project
from app.models.todo import Todo, TodoStatus, TodoPriority
from app.services.password import hash_password


class TestTodoAccess:
    """Tests for todo access control."""

    def test_todos_require_auth(self, client):
        """Should require authentication for todos."""
        response = client.get("/todos", follow_redirects=False)
        assert response.status_code == 401


class TestTodoList:
    """Tests for todo list page."""

    def test_list_todos(self, client, db_session):
        """Should list todos."""
        user = User(
            email="user@example.com",
            name="Test User",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        todo = Todo(
            title="Test Todo",
            description="A test todo",
            created_by=user.id,
        )
        db_session.add(todo)
        db_session.commit()

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.get("/todos")
        assert response.status_code == 200
        assert "Test Todo" in response.text

    def test_list_todos_empty(self, client, db_session):
        """Should handle no todos."""
        user = User(
            email="user@example.com",
            name="Test User",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.get("/todos")
        assert response.status_code == 200
        assert "No todos found" in response.text


class TestCreateTodo:
    """Tests for creating todos."""

    def test_create_todo_form(self, client, db_session):
        """Should show create todo form."""
        user = User(
            email="user@example.com",
            name="Test User",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.get("/todos/new")
        assert response.status_code == 200
        assert "New Todo" in response.text

    def test_create_todo_success(self, client, db_session):
        """Should create a todo."""
        user = User(
            email="user@example.com",
            name="Test User",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.post(
            "/todos/new",
            data={
                "title": "New Todo",
                "description": "A new todo",
                "priority": "high",
            },
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert "/todos/" in response.headers.get("location", "")

    def test_create_todo_with_project(self, client, db_session):
        """Should create todo linked to project."""
        user = User(
            email="user@example.com",
            name="Test User",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        project = Project(name="Test Project", created_by=user.id)
        db_session.add(project)
        db_session.commit()

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.post(
            "/todos/new",
            data={
                "title": "Project Todo",
                "project_id": str(project.id),
            },
            follow_redirects=False,
        )

        assert response.status_code == 302


class TestViewTodo:
    """Tests for viewing todo details."""

    def test_view_todo(self, client, db_session):
        """Should view todo details."""
        user = User(
            email="user@example.com",
            name="Test User",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        todo = Todo(
            title="Test Todo",
            description="A test todo",
            created_by=user.id,
        )
        db_session.add(todo)
        db_session.commit()

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.get(f"/todos/{todo.id}")
        assert response.status_code == 200
        assert "Test Todo" in response.text
        assert "A test todo" in response.text

    def test_view_nonexistent_todo(self, client, db_session):
        """Should redirect for nonexistent todo."""
        user = User(
            email="user@example.com",
            name="Test User",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        import uuid

        response = client.get(f"/todos/{uuid.uuid4()}", follow_redirects=False)
        assert response.status_code == 302


class TestEditTodo:
    """Tests for editing todos."""

    def test_edit_todo_form(self, client, db_session):
        """Should show edit form."""
        user = User(
            email="user@example.com",
            name="Test User",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        todo = Todo(
            title="Test Todo",
            created_by=user.id,
        )
        db_session.add(todo)
        db_session.commit()

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.get(f"/todos/{todo.id}/edit")
        assert response.status_code == 200
        assert "Edit Todo" in response.text
        assert "Test Todo" in response.text

    def test_edit_todo_success(self, client, db_session):
        """Should update todo."""
        user = User(
            email="user@example.com",
            name="Test User",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        todo = Todo(
            title="Test Todo",
            created_by=user.id,
        )
        db_session.add(todo)
        db_session.commit()
        todo_id = todo.id

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.post(
            f"/todos/{todo_id}/edit",
            data={
                "title": "Updated Title",
                "description": "Updated description",
                "priority": "high",
                "status": "in_progress",
            },
            follow_redirects=False,
        )

        assert response.status_code == 302

        db_session.refresh(todo)
        assert todo.title == "Updated Title"
        assert todo.status == TodoStatus.IN_PROGRESS


class TestDeleteTodo:
    """Tests for deleting todos."""

    def test_delete_todo(self, client, db_session):
        """Should delete todo."""
        user = User(
            email="user@example.com",
            name="Test User",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        todo = Todo(
            title="Test Todo",
            created_by=user.id,
        )
        db_session.add(todo)
        db_session.commit()
        todo_id = todo.id

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.post(
            f"/todos/{todo_id}/delete",
            follow_redirects=False,
        )

        assert response.status_code == 302

        db_session.expire_all()
        deleted = db_session.get(Todo, todo_id)
        assert deleted is None


class TestChangeStatus:
    """Tests for changing todo status."""

    def test_change_status(self, client, db_session):
        """Should change status via inline update."""
        user = User(
            email="user@example.com",
            name="Test User",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        todo = Todo(
            title="Test Todo",
            created_by=user.id,
        )
        db_session.add(todo)
        db_session.commit()
        todo_id = todo.id

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.post(
            f"/todos/{todo_id}/status",
            data={"status": "done"},
        )

        assert response.status_code == 200

        db_session.refresh(todo)
        assert todo.status == TodoStatus.DONE
