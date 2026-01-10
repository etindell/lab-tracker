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


class TestKanbanBoard:
    """Tests for kanban board view."""

    def test_kanban_board_requires_auth(self, client):
        """Should require authentication for kanban."""
        response = client.get("/todos/kanban", follow_redirects=False)
        assert response.status_code == 401

    def test_kanban_board_renders(self, client, db_session):
        """Should render kanban board."""
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

        response = client.get("/todos/kanban")
        assert response.status_code == 200
        assert "Kanban Board" in response.text

    def test_kanban_board_shows_columns(self, client, db_session):
        """Should show all status columns."""
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

        response = client.get("/todos/kanban")
        assert response.status_code == 200
        assert "Open" in response.text
        assert "In Progress" in response.text
        assert "Blocked" in response.text
        assert "Done" in response.text

    def test_kanban_board_with_todos(self, client, db_session):
        """Should display todos in correct columns."""
        user = User(
            email="user@example.com",
            name="Test User",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        open_todo = Todo(
            title="Open Task",
            created_by=user.id,
            assigned_to=user.id,
            status=TodoStatus.OPEN,
        )
        in_progress_todo = Todo(
            title="In Progress Task",
            created_by=user.id,
            assigned_to=user.id,
            status=TodoStatus.IN_PROGRESS,
        )
        done_todo = Todo(
            title="Done Task",
            created_by=user.id,
            assigned_to=user.id,
            status=TodoStatus.DONE,
        )
        db_session.add_all([open_todo, in_progress_todo, done_todo])
        db_session.commit()

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.get("/todos/kanban")
        assert response.status_code == 200
        assert "Open Task" in response.text
        assert "In Progress Task" in response.text
        assert "Done Task" in response.text

    def test_kanban_board_filter_by_project(self, client, db_session):
        """Should filter todos by project."""
        user = User(
            email="user@example.com",
            name="Test User",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        project1 = Project(name="Project A", created_by=user.id)
        project2 = Project(name="Project B", created_by=user.id)
        db_session.add_all([project1, project2])
        db_session.commit()

        todo1 = Todo(
            title="Project A Task",
            created_by=user.id,
            assigned_to=user.id,
            project_id=project1.id,
        )
        todo2 = Todo(
            title="Project B Task",
            created_by=user.id,
            assigned_to=user.id,
            project_id=project2.id,
        )
        db_session.add_all([todo1, todo2])
        db_session.commit()

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.get(f"/todos/kanban?project_id={project1.id}")
        assert response.status_code == 200
        assert "Project A Task" in response.text
        assert "Project B Task" not in response.text

    def test_kanban_board_my_todos_filter(self, client, db_session):
        """Should filter to show only user's created or assigned todos."""
        user1 = User(
            email="user1@example.com",
            name="User One",
            password_hash=hash_password("password"),
        )
        user2 = User(
            email="user2@example.com",
            name="User Two",
            password_hash=hash_password("password"),
        )
        db_session.add_all([user1, user2])
        db_session.commit()

        my_todo = Todo(
            title="My Task",
            created_by=user1.id,
            assigned_to=user1.id,
        )
        # Created by user2, assigned to user2 - should not appear for user1
        other_todo = Todo(
            title="Other Task",
            created_by=user2.id,
            assigned_to=user2.id,
        )
        db_session.add_all([my_todo, other_todo])
        db_session.commit()

        client.post(
            "/login",
            data={"email": "user1@example.com", "password": "password"},
        )

        # With my_todos=true (default) - shows todos created by or assigned to user
        response = client.get("/todos/kanban?my_todos=true")
        assert response.status_code == 200
        assert "My Task" in response.text
        assert "Other Task" not in response.text

        # With my_todos=false - shows all todos
        response = client.get("/todos/kanban?my_todos=false")
        assert response.status_code == 200
        assert "My Task" in response.text
        assert "Other Task" in response.text

    def test_kanban_drag_drop_status_change(self, client, db_session):
        """Should change status when card is dragged to new column."""
        user = User(
            email="user@example.com",
            name="Test User",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        todo = Todo(
            title="Draggable Task",
            created_by=user.id,
            status=TodoStatus.OPEN,
        )
        db_session.add(todo)
        db_session.commit()
        todo_id = todo.id

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        # Simulate drag-drop by calling status endpoint
        response = client.post(
            f"/todos/{todo_id}/status",
            data={"status": "in_progress"},
        )
        assert response.status_code == 200

        db_session.refresh(todo)
        assert todo.status == TodoStatus.IN_PROGRESS
