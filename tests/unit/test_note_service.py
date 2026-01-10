"""Unit tests for note service."""

import pytest
from sqlalchemy.orm import Session

from app.models.experiment import Experiment, ExperimentStatus
from app.models.note import Note
from app.models.project import Project
from app.models.replicate import Replicate
from app.models.user import User
from app.services.note import NoteService
from app.services.password import hash_password


@pytest.fixture
def user(db_session: Session) -> User:
    """Create a test user."""
    user = User(
        email="user@example.com",
        name="Test User",
        password_hash=hash_password("password"),
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def project(db_session: Session, user: User) -> Project:
    """Create a test project."""
    project = Project(name="Test Project", created_by=user.id)
    db_session.add(project)
    db_session.commit()
    return project


@pytest.fixture
def experiment(db_session: Session, user: User, project: Project) -> Experiment:
    """Create a test experiment."""
    experiment = Experiment(
        name="Test Experiment",
        project_id=project.id,
        created_by=user.id,
    )
    db_session.add(experiment)
    db_session.commit()
    return experiment


@pytest.fixture
def replicate(db_session: Session, experiment: Experiment) -> Replicate:
    """Create a test replicate."""
    replicate = Replicate(
        name="Test Replicate",
        experiment_id=experiment.id,
    )
    db_session.add(replicate)
    db_session.commit()
    return replicate


class TestNoteServiceCreate:
    """Tests for creating notes."""

    def test_create_note_on_experiment(
        self, db_session: Session, user: User, experiment: Experiment
    ):
        """Should create a note attached to experiment."""
        service = NoteService(db_session)

        note = service.create_note(
            content="# Test Note\n\nThis is a test note.",
            author=user,
            experiment=experiment,
        )

        assert note.id is not None
        assert note.content == "# Test Note\n\nThis is a test note."
        assert note.author_id == user.id
        assert note.experiment_id == experiment.id
        assert note.replicate_id is None

    def test_create_note_on_replicate(
        self, db_session: Session, user: User, replicate: Replicate
    ):
        """Should create a note attached to replicate."""
        service = NoteService(db_session)

        note = service.create_note(
            content="Replicate note content",
            author=user,
            replicate=replicate,
        )

        assert note.id is not None
        assert note.content == "Replicate note content"
        assert note.author_id == user.id
        assert note.experiment_id is None
        assert note.replicate_id == replicate.id

    def test_create_note_requires_parent(
        self, db_session: Session, user: User
    ):
        """Should raise error if no experiment or replicate provided."""
        service = NoteService(db_session)

        with pytest.raises(ValueError, match="must be attached"):
            service.create_note(
                content="Orphan note",
                author=user,
            )


class TestNoteServiceList:
    """Tests for listing notes."""

    def test_list_notes_by_experiment(
        self, db_session: Session, user: User, experiment: Experiment
    ):
        """Should list notes for an experiment."""
        service = NoteService(db_session)

        note1 = service.create_note(
            content="First note",
            author=user,
            experiment=experiment,
        )
        note2 = service.create_note(
            content="Second note",
            author=user,
            experiment=experiment,
        )

        notes = service.list_notes(experiment=experiment)

        assert len(notes) == 2
        # Notes are ordered by created_at desc (newest first)
        assert notes[0].content == "Second note"
        assert notes[1].content == "First note"

    def test_list_notes_by_replicate(
        self, db_session: Session, user: User, replicate: Replicate
    ):
        """Should list notes for a replicate."""
        service = NoteService(db_session)

        service.create_note(
            content="Replicate note",
            author=user,
            replicate=replicate,
        )

        notes = service.list_notes(replicate=replicate)

        assert len(notes) == 1
        assert notes[0].content == "Replicate note"


class TestNoteServiceGet:
    """Tests for getting a single note."""

    def test_get_by_id(
        self, db_session: Session, user: User, experiment: Experiment
    ):
        """Should get note by ID."""
        service = NoteService(db_session)

        created = service.create_note(
            content="Test note",
            author=user,
            experiment=experiment,
        )

        note = service.get_by_id(created.id)

        assert note is not None
        assert note.id == created.id

    def test_get_by_id_not_found(self, db_session: Session):
        """Should return None for non-existent note."""
        import uuid

        service = NoteService(db_session)

        note = service.get_by_id(uuid.uuid4())

        assert note is None


class TestNoteServiceUpdate:
    """Tests for updating notes."""

    def test_update_note_content(
        self, db_session: Session, user: User, experiment: Experiment
    ):
        """Should update note content."""
        service = NoteService(db_session)

        note = service.create_note(
            content="Original content",
            author=user,
            experiment=experiment,
        )

        updated = service.update_note(note, content="Updated content")

        assert updated.content == "Updated content"

    def test_update_note_no_change(
        self, db_session: Session, user: User, experiment: Experiment
    ):
        """Should handle update with no changes."""
        service = NoteService(db_session)

        note = service.create_note(
            content="Original content",
            author=user,
            experiment=experiment,
        )

        updated = service.update_note(note)

        assert updated.content == "Original content"


class TestNoteServiceDelete:
    """Tests for deleting notes."""

    def test_delete_note(
        self, db_session: Session, user: User, experiment: Experiment
    ):
        """Should delete a note."""
        service = NoteService(db_session)

        note = service.create_note(
            content="To be deleted",
            author=user,
            experiment=experiment,
        )
        note_id = note.id

        service.delete_note(note)

        db_session.expire_all()
        deleted = service.get_by_id(note_id)
        assert deleted is None
