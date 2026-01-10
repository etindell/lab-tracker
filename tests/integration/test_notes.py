"""Integration tests for note routes."""

import pytest
import uuid

from app.models.experiment import Experiment
from app.models.note import Note
from app.models.project import Project
from app.models.replicate import Replicate
from app.models.user import User
from app.services.password import hash_password


class TestNoteAccess:
    """Tests for note access control."""

    def test_notes_require_auth(self, client, db_session):
        """Should require authentication for notes."""
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

        response = client.post(
            f"/projects/{project.id}/experiments/{experiment.id}/notes/new",
            data={"content": "Test note"},
            follow_redirects=False,
        )
        assert response.status_code == 401


class TestCreateNoteOnExperiment:
    """Tests for creating notes on experiments."""

    def test_create_note_success(self, client, db_session):
        """Should create a note on experiment."""
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
            f"/projects/{project.id}/experiments/{experiment.id}/notes/new",
            data={"content": "# Test Note\n\nThis is a test note."},
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert f"/projects/{project.id}/experiments/{experiment.id}" in response.headers.get("location", "")

        # Check note was created
        notes = db_session.query(Note).filter(Note.experiment_id == experiment.id).all()
        assert len(notes) == 1
        assert notes[0].content == "# Test Note\n\nThis is a test note."

    def test_create_note_empty_content(self, client, db_session):
        """Should reject empty note content."""
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
            f"/projects/{project.id}/experiments/{experiment.id}/notes/new",
            data={"content": ""},
            follow_redirects=False,
        )

        # Should redirect back without creating note
        assert response.status_code == 302
        notes = db_session.query(Note).filter(Note.experiment_id == experiment.id).all()
        assert len(notes) == 0


class TestCreateNoteOnReplicate:
    """Tests for creating notes on replicates."""

    def test_create_note_on_replicate(self, client, db_session):
        """Should create a note on replicate."""
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

        response = client.post(
            f"/projects/{project.id}/experiments/{experiment.id}/replicates/{replicate.id}/notes/new",
            data={"content": "Replicate observation note"},
            follow_redirects=False,
        )

        assert response.status_code == 302

        # Check note was created
        notes = db_session.query(Note).filter(Note.replicate_id == replicate.id).all()
        assert len(notes) == 1
        assert notes[0].content == "Replicate observation note"


class TestEditNote:
    """Tests for editing notes."""

    def test_edit_note_form(self, client, db_session):
        """Should show edit note form."""
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

        note = Note(
            content="Original content",
            author_id=user.id,
            experiment_id=experiment.id,
        )
        db_session.add(note)
        db_session.commit()

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.get(
            f"/projects/{project.id}/experiments/{experiment.id}/notes/{note.id}/edit"
        )

        assert response.status_code == 200
        assert "Original content" in response.text
        assert "Edit Note" in response.text

    def test_edit_note_success(self, client, db_session):
        """Should update note content."""
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

        note = Note(
            content="Original content",
            author_id=user.id,
            experiment_id=experiment.id,
        )
        db_session.add(note)
        db_session.commit()
        note_id = note.id

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.post(
            f"/projects/{project.id}/experiments/{experiment.id}/notes/{note_id}/edit",
            data={"content": "Updated content"},
            follow_redirects=False,
        )

        assert response.status_code == 302

        db_session.refresh(note)
        assert note.content == "Updated content"


class TestDeleteNote:
    """Tests for deleting notes."""

    def test_delete_note(self, client, db_session):
        """Should delete a note."""
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

        note = Note(
            content="To be deleted",
            author_id=user.id,
            experiment_id=experiment.id,
        )
        db_session.add(note)
        db_session.commit()
        note_id = note.id

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.post(
            f"/projects/{project.id}/experiments/{experiment.id}/notes/{note_id}/delete",
            follow_redirects=False,
        )

        assert response.status_code == 302

        db_session.expire_all()
        deleted = db_session.get(Note, note_id)
        assert deleted is None


class TestNotesOnExperimentDetail:
    """Tests for viewing notes on experiment detail page."""

    def test_notes_displayed_on_experiment(self, client, db_session):
        """Should display notes on experiment detail page."""
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

        note = Note(
            content="# Important Finding\n\nThis is a key observation.",
            author_id=user.id,
            experiment_id=experiment.id,
        )
        db_session.add(note)
        db_session.commit()

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.get(f"/projects/{project.id}/experiments/{experiment.id}")

        assert response.status_code == 200
        assert "Important Finding" in response.text
        assert "This is a key observation" in response.text


class TestNotesOnReplicateDetail:
    """Tests for viewing notes on replicate detail page."""

    def test_notes_displayed_on_replicate(self, client, db_session):
        """Should display notes on replicate detail page."""
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

        note = Note(
            content="Replicate observation note",
            author_id=user.id,
            replicate_id=replicate.id,
        )
        db_session.add(note)
        db_session.commit()

        client.post(
            "/login",
            data={"email": "user@example.com", "password": "password"},
        )

        response = client.get(
            f"/projects/{project.id}/experiments/{experiment.id}/replicates/{replicate.id}"
        )

        assert response.status_code == 200
        assert "Replicate observation note" in response.text
