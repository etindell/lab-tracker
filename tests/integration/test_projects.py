"""Integration tests for project routes."""

import pytest

from app.models.user import User
from app.models.project import Project, ProjectStatus
from app.services.password import hash_password


class TestProjectAccess:
    """Tests for project access control."""

    def test_projects_require_auth(self, client):
        """Should require authentication for projects."""
        response = client.get("/projects", follow_redirects=False)
        # Should return 401 Unauthorized
        assert response.status_code == 401


class TestProjectList:
    """Tests for project list page."""

    def test_list_projects(self, client, db_session):
        """Should list projects."""
        user = User(
            email="user@example.com",
            name="Test User",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        project = Project(
            name="Test Project",
            description="A test project",
            created_by=user.id,
        )
        db_session.add(project)
        db_session.commit()

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.get("/projects")
        assert response.status_code == 200
        assert "Test Project" in response.text

    def test_list_projects_empty(self, client, db_session):
        """Should handle no projects."""
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

        response = client.get("/projects")
        assert response.status_code == 200
        assert "No projects found" in response.text


class TestCreateProject:
    """Tests for creating projects."""

    def test_create_project_form(self, client, db_session):
        """Should show create project form."""
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

        response = client.get("/projects/new")
        assert response.status_code == 200
        assert "New Project" in response.text

    def test_create_project_success(self, client, db_session):
        """Should create a project."""
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
            "/projects/new",
            data={
                "name": "New Project",
                "description": "A new project",
                "project_status": "active",
            },
            follow_redirects=False,
        )

        assert response.status_code == 302
        # Should redirect to project detail
        assert "/projects/" in response.headers.get("location", "")

    def test_create_project_duplicate_name(self, client, db_session):
        """Should reject duplicate name."""
        user = User(
            email="user@example.com",
            name="Test User",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        existing = Project(
            name="Existing Project",
            created_by=user.id,
        )
        db_session.add(existing)
        db_session.commit()

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.post(
            "/projects/new",
            data={
                "name": "Existing Project",
                "description": "Duplicate",
            },
        )

        assert response.status_code == 400
        assert "already exists" in response.text


class TestViewProject:
    """Tests for viewing project details."""

    def test_view_project(self, client, db_session):
        """Should view project details."""
        user = User(
            email="user@example.com",
            name="Test User",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        project = Project(
            name="Test Project",
            description="A test project",
            created_by=user.id,
        )
        db_session.add(project)
        db_session.commit()

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.get(f"/projects/{project.id}")
        assert response.status_code == 200
        assert "Test Project" in response.text
        assert "A test project" in response.text

    def test_view_nonexistent_project(self, client, db_session):
        """Should redirect for nonexistent project."""
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
        response = client.get(f"/projects/{uuid.uuid4()}", follow_redirects=False)
        assert response.status_code == 302


class TestEditProject:
    """Tests for editing projects."""

    def test_edit_project_form(self, client, db_session):
        """Should show edit form."""
        user = User(
            email="user@example.com",
            name="Test User",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        project = Project(
            name="Test Project",
            description="A test project",
            created_by=user.id,
        )
        db_session.add(project)
        db_session.commit()

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.get(f"/projects/{project.id}/edit")
        assert response.status_code == 200
        assert "Edit Project" in response.text
        assert "Test Project" in response.text

    def test_edit_project_success(self, client, db_session):
        """Should update project."""
        user = User(
            email="user@example.com",
            name="Test User",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        project = Project(
            name="Test Project",
            created_by=user.id,
        )
        db_session.add(project)
        db_session.commit()
        project_id = project.id

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.post(
            f"/projects/{project_id}/edit",
            data={
                "name": "Updated Name",
                "description": "Updated description",
                "project_status": "on_hold",
            },
            follow_redirects=False,
        )

        assert response.status_code == 302

        # Verify update
        db_session.refresh(project)
        assert project.name == "Updated Name"
        assert project.status == ProjectStatus.ON_HOLD


class TestArchiveProject:
    """Tests for archiving projects."""

    def test_archive_project(self, client, db_session):
        """Should archive project."""
        user = User(
            email="user@example.com",
            name="Test User",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        project = Project(
            name="Test Project",
            created_by=user.id,
        )
        db_session.add(project)
        db_session.commit()
        project_id = project.id

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.post(
            f"/projects/{project_id}/archive",
            follow_redirects=False,
        )

        assert response.status_code == 302

        db_session.refresh(project)
        assert project.status == ProjectStatus.ARCHIVED
