"""Integration tests for replicate routes."""

import pytest

from app.models.user import User
from app.models.project import Project
from app.models.experiment import Experiment
from app.models.replicate import Replicate, ReplicateStatus
from app.services.password import hash_password


class TestReplicateAccess:
    """Tests for replicate access control."""

    def test_replicates_require_auth(self, client, db_session):
        """Should require authentication for replicates."""
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

        response = client.get(
            f"/projects/{project.id}/experiments/{experiment.id}/replicates",
            follow_redirects=False,
        )
        assert response.status_code == 401


class TestReplicateList:
    """Tests for replicate list page."""

    def test_list_replicates(self, client, db_session):
        """Should list replicates for an experiment."""
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

        replicate = Replicate(
            name="Test Replicate",
            summary="A test replicate",
            experiment_id=experiment.id,
        )
        db_session.add(replicate)
        db_session.commit()

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.get(
            f"/projects/{project.id}/experiments/{experiment.id}/replicates"
        )
        assert response.status_code == 200
        assert "Test Replicate" in response.text

    def test_list_replicates_empty(self, client, db_session):
        """Should handle no replicates."""
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

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.get(
            f"/projects/{project.id}/experiments/{experiment.id}/replicates"
        )
        assert response.status_code == 200
        assert "No replicates found" in response.text


class TestCreateReplicate:
    """Tests for creating replicates."""

    def test_create_replicate_form(self, client, db_session):
        """Should show create replicate form."""
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

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.get(
            f"/projects/{project.id}/experiments/{experiment.id}/replicates/new"
        )
        assert response.status_code == 200
        assert "New Replicate" in response.text

    def test_create_replicate_success(self, client, db_session):
        """Should create a replicate."""
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

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.post(
            f"/projects/{project.id}/experiments/{experiment.id}/replicates/new",
            data={
                "name": "New Replicate",
                "summary": "A new replicate",
                "replicate_status": "planned",
            },
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert "/replicates/" in response.headers.get("location", "")


class TestViewReplicate:
    """Tests for viewing replicate details."""

    def test_view_replicate(self, client, db_session):
        """Should view replicate details."""
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

        replicate = Replicate(
            name="Test Replicate",
            summary="A test replicate",
            experiment_id=experiment.id,
        )
        db_session.add(replicate)
        db_session.commit()

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.get(
            f"/projects/{project.id}/experiments/{experiment.id}/replicates/{replicate.id}"
        )
        assert response.status_code == 200
        assert "Test Replicate" in response.text
        assert "A test replicate" in response.text

    def test_view_nonexistent_replicate(self, client, db_session):
        """Should redirect for nonexistent replicate."""
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

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        import uuid

        response = client.get(
            f"/projects/{project.id}/experiments/{experiment.id}/replicates/{uuid.uuid4()}",
            follow_redirects=False,
        )
        assert response.status_code == 302


class TestEditReplicate:
    """Tests for editing replicates."""

    def test_edit_replicate_form(self, client, db_session):
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
            project_id=project.id,
            created_by=user.id,
        )
        db_session.add(experiment)
        db_session.commit()

        replicate = Replicate(
            name="Test Replicate",
            experiment_id=experiment.id,
        )
        db_session.add(replicate)
        db_session.commit()

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.get(
            f"/projects/{project.id}/experiments/{experiment.id}/replicates/{replicate.id}/edit"
        )
        assert response.status_code == 200
        assert "Edit Replicate" in response.text
        assert "Test Replicate" in response.text

    def test_edit_replicate_success(self, client, db_session):
        """Should update replicate."""
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

        replicate = Replicate(
            name="Test Replicate",
            experiment_id=experiment.id,
        )
        db_session.add(replicate)
        db_session.commit()
        replicate_id = replicate.id

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.post(
            f"/projects/{project.id}/experiments/{experiment.id}/replicates/{replicate_id}/edit",
            data={
                "name": "Updated Name",
                "summary": "Updated summary",
                "replicate_status": "in_progress",
            },
            follow_redirects=False,
        )

        assert response.status_code == 302

        db_session.refresh(replicate)
        assert replicate.name == "Updated Name"
        assert replicate.status == ReplicateStatus.IN_PROGRESS


class TestDeleteReplicate:
    """Tests for deleting replicates."""

    def test_delete_replicate(self, client, db_session):
        """Should delete replicate."""
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

        replicate = Replicate(
            name="Test Replicate",
            experiment_id=experiment.id,
        )
        db_session.add(replicate)
        db_session.commit()
        replicate_id = replicate.id

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.post(
            f"/projects/{project.id}/experiments/{experiment.id}/replicates/{replicate_id}/delete",
            follow_redirects=False,
        )

        assert response.status_code == 302

        db_session.expire_all()
        deleted = db_session.get(Replicate, replicate_id)
        assert deleted is None


class TestInlineStatusChange:
    """Tests for inline status change via HTMX."""

    def test_change_status_inline(self, client, db_session):
        """Should change status via inline update."""
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

        replicate = Replicate(
            name="Test Replicate",
            experiment_id=experiment.id,
        )
        db_session.add(replicate)
        db_session.commit()
        replicate_id = replicate.id

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.post(
            f"/projects/{project.id}/experiments/{experiment.id}/replicates/{replicate_id}/status",
            data={"status": "in_progress"},
        )

        assert response.status_code == 200

        db_session.refresh(replicate)
        assert replicate.status == ReplicateStatus.IN_PROGRESS

    def test_change_status_to_done(self, client, db_session):
        """Should change status to done."""
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

        replicate = Replicate(
            name="Test Replicate",
            experiment_id=experiment.id,
            status=ReplicateStatus.IN_PROGRESS,
        )
        db_session.add(replicate)
        db_session.commit()
        replicate_id = replicate.id

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.post(
            f"/projects/{project.id}/experiments/{experiment.id}/replicates/{replicate_id}/status",
            data={"status": "done"},
        )

        assert response.status_code == 200

        db_session.refresh(replicate)
        assert replicate.status == ReplicateStatus.DONE
