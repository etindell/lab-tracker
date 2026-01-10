"""Integration tests for experiment routes."""

import pytest

from app.models.user import User
from app.models.project import Project
from app.models.experiment import Experiment, ExperimentStatus
from app.services.password import hash_password


class TestExperimentAccess:
    """Tests for experiment access control."""

    def test_experiments_require_auth(self, client, db_session):
        """Should require authentication for experiments."""
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

        response = client.get(
            f"/projects/{project.id}/experiments", follow_redirects=False
        )
        assert response.status_code == 401


class TestExperimentList:
    """Tests for experiment list page."""

    def test_list_experiments(self, client, db_session):
        """Should list experiments for a project."""
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

        experiment = Experiment(
            name="Test Experiment",
            description="A test experiment",
            project_id=project.id,
            created_by=user.id,
        )
        db_session.add(experiment)
        db_session.commit()

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.get(f"/projects/{project.id}/experiments")
        assert response.status_code == 200
        assert "Test Experiment" in response.text

    def test_list_experiments_empty(self, client, db_session):
        """Should handle no experiments."""
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

        response = client.get(f"/projects/{project.id}/experiments")
        assert response.status_code == 200
        assert "No experiments found" in response.text


class TestCreateExperiment:
    """Tests for creating experiments."""

    def test_create_experiment_form(self, client, db_session):
        """Should show create experiment form."""
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

        response = client.get(f"/projects/{project.id}/experiments/new")
        assert response.status_code == 200
        assert "New Experiment" in response.text

    def test_create_experiment_success(self, client, db_session):
        """Should create an experiment."""
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
            f"/projects/{project.id}/experiments/new",
            data={
                "name": "New Experiment",
                "description": "A new experiment",
                "experiment_status": "planned",
            },
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert "/experiments/" in response.headers.get("location", "")

    def test_create_experiment_duplicate_name(self, client, db_session):
        """Should reject duplicate name within project."""
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

        existing = Experiment(
            name="Existing Experiment",
            project_id=project.id,
            created_by=user.id,
        )
        db_session.add(existing)
        db_session.commit()

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.post(
            f"/projects/{project.id}/experiments/new",
            data={
                "name": "Existing Experiment",
                "description": "Duplicate",
            },
        )

        assert response.status_code == 400
        assert "already exists" in response.text


class TestViewExperiment:
    """Tests for viewing experiment details."""

    def test_view_experiment(self, client, db_session):
        """Should view experiment details."""
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

        experiment = Experiment(
            name="Test Experiment",
            description="A test experiment",
            project_id=project.id,
            created_by=user.id,
        )
        db_session.add(experiment)
        db_session.commit()

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.get(
            f"/projects/{project.id}/experiments/{experiment.id}"
        )
        assert response.status_code == 200
        assert "Test Experiment" in response.text
        assert "A test experiment" in response.text

    def test_view_nonexistent_experiment(self, client, db_session):
        """Should redirect for nonexistent experiment."""
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

        import uuid

        response = client.get(
            f"/projects/{project.id}/experiments/{uuid.uuid4()}",
            follow_redirects=False,
        )
        assert response.status_code == 302


class TestEditExperiment:
    """Tests for editing experiments."""

    def test_edit_experiment_form(self, client, db_session):
        """Should show edit form."""
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

        experiment = Experiment(
            name="Test Experiment",
            description="A test experiment",
            project_id=project.id,
            created_by=user.id,
        )
        db_session.add(experiment)
        db_session.commit()

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.get(
            f"/projects/{project.id}/experiments/{experiment.id}/edit"
        )
        assert response.status_code == 200
        assert "Edit Experiment" in response.text
        assert "Test Experiment" in response.text

    def test_edit_experiment_success(self, client, db_session):
        """Should update experiment."""
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

        experiment = Experiment(
            name="Test Experiment",
            project_id=project.id,
            created_by=user.id,
        )
        db_session.add(experiment)
        db_session.commit()
        experiment_id = experiment.id

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.post(
            f"/projects/{project.id}/experiments/{experiment_id}/edit",
            data={
                "name": "Updated Name",
                "description": "Updated description",
                "experiment_status": "running",
            },
            follow_redirects=False,
        )

        assert response.status_code == 302

        db_session.refresh(experiment)
        assert experiment.name == "Updated Name"
        assert experiment.status == ExperimentStatus.RUNNING


class TestArchiveExperiment:
    """Tests for archiving experiments."""

    def test_archive_experiment(self, client, db_session):
        """Should archive experiment."""
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

        experiment = Experiment(
            name="Test Experiment",
            project_id=project.id,
            created_by=user.id,
        )
        db_session.add(experiment)
        db_session.commit()
        experiment_id = experiment.id

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.post(
            f"/projects/{project.id}/experiments/{experiment_id}/archive",
            follow_redirects=False,
        )

        assert response.status_code == 302

        db_session.refresh(experiment)
        assert experiment.status == ExperimentStatus.ARCHIVED


class TestDeleteExperiment:
    """Tests for deleting experiments."""

    def test_delete_experiment(self, client, db_session):
        """Should delete experiment."""
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

        experiment = Experiment(
            name="Test Experiment",
            project_id=project.id,
            created_by=user.id,
        )
        db_session.add(experiment)
        db_session.commit()
        experiment_id = experiment.id

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.post(
            f"/projects/{project.id}/experiments/{experiment_id}/delete",
            follow_redirects=False,
        )

        assert response.status_code == 302

        # Expire session cache to get fresh data from DB
        db_session.expire_all()
        deleted = db_session.get(Experiment, experiment_id)
        assert deleted is None
