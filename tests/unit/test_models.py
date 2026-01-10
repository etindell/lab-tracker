"""Unit tests for database models."""

import uuid
from datetime import datetime, timezone

import pytest

from app.models.user import User
from app.models.project import Project, ProjectStatus
from app.models.experiment import Experiment, ExperimentStatus
from app.models.replicate import Replicate, ReplicateStatus
from app.models.todo import Todo, TodoStatus, TodoPriority
from app.models.note import Note
from app.models.activity import ActivityLog


class TestUserModel:
    """Tests for User model."""

    def test_create_user(self, db_session):
        """Should create a user with required fields."""
        user = User(
            email="test@example.com",
            name="Test User",
            password_hash="hashed_password",
        )
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.is_admin is False
        assert user.is_active is True
        assert user.created_at is not None

    def test_user_email_unique(self, db_session):
        """Should enforce unique email constraint."""
        user1 = User(
            email="unique@example.com",
            name="User 1",
            password_hash="hash1",
        )
        db_session.add(user1)
        db_session.commit()

        user2 = User(
            email="unique@example.com",
            name="User 2",
            password_hash="hash2",
        )
        db_session.add(user2)

        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()

    def test_user_repr(self, db_session):
        """User repr should show email."""
        user = User(
            email="repr@example.com",
            name="Test",
            password_hash="hash",
        )
        assert "repr@example.com" in repr(user)


class TestProjectModel:
    """Tests for Project model."""

    def test_create_project(self, db_session):
        """Should create a project with required fields."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash="hash",
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

        assert project.id is not None
        assert project.name == "Test Project"
        assert project.status == ProjectStatus.ACTIVE
        assert project.created_by == user.id

    def test_project_name_unique(self, db_session):
        """Should enforce unique project name."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash="hash",
        )
        db_session.add(user)
        db_session.commit()

        project1 = Project(name="Unique Name", created_by=user.id)
        db_session.add(project1)
        db_session.commit()

        project2 = Project(name="Unique Name", created_by=user.id)
        db_session.add(project2)

        with pytest.raises(Exception):
            db_session.commit()

    def test_project_status_enum(self, db_session):
        """Should accept valid status values."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash="hash",
        )
        db_session.add(user)
        db_session.commit()

        for status in ProjectStatus:
            project = Project(
                name=f"Project {status.value}",
                status=status,
                created_by=user.id,
            )
            db_session.add(project)
            db_session.commit()
            assert project.status == status


class TestExperimentModel:
    """Tests for Experiment model."""

    def test_create_experiment(self, db_session):
        """Should create an experiment within a project."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash="hash",
        )
        db_session.add(user)
        db_session.commit()

        project = Project(name="Test Project", created_by=user.id)
        db_session.add(project)
        db_session.commit()

        experiment = Experiment(
            name="Test Experiment",
            description="Testing",
            project_id=project.id,
            created_by=user.id,
        )
        db_session.add(experiment)
        db_session.commit()

        assert experiment.id is not None
        assert experiment.status == ExperimentStatus.PLANNED
        assert experiment.project_id == project.id

    def test_experiment_unique_name_per_project(self, db_session):
        """Should enforce unique name within project."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash="hash",
        )
        db_session.add(user)
        db_session.commit()

        project = Project(name="Test Project", created_by=user.id)
        db_session.add(project)
        db_session.commit()

        exp1 = Experiment(
            name="Same Name",
            project_id=project.id,
            created_by=user.id,
        )
        db_session.add(exp1)
        db_session.commit()

        exp2 = Experiment(
            name="Same Name",
            project_id=project.id,
            created_by=user.id,
        )
        db_session.add(exp2)

        with pytest.raises(Exception):
            db_session.commit()

    def test_experiment_same_name_different_projects(self, db_session):
        """Should allow same name in different projects."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash="hash",
        )
        db_session.add(user)
        db_session.commit()

        project1 = Project(name="Project 1", created_by=user.id)
        project2 = Project(name="Project 2", created_by=user.id)
        db_session.add_all([project1, project2])
        db_session.commit()

        exp1 = Experiment(
            name="Same Name",
            project_id=project1.id,
            created_by=user.id,
        )
        exp2 = Experiment(
            name="Same Name",
            project_id=project2.id,
            created_by=user.id,
        )
        db_session.add_all([exp1, exp2])
        db_session.commit()

        assert exp1.id != exp2.id


class TestReplicateModel:
    """Tests for Replicate model."""

    def test_create_replicate(self, db_session):
        """Should create a replicate within an experiment."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash="hash",
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
            name="Run 1",
            experiment_id=experiment.id,
            performed_by=user.id,
        )
        db_session.add(replicate)
        db_session.commit()

        assert replicate.id is not None
        assert replicate.status == ReplicateStatus.PLANNED
        assert replicate.experiment_id == experiment.id

    def test_replicate_status_values(self, db_session):
        """Should accept all valid status values."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash="hash",
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

        for status in ReplicateStatus:
            replicate = Replicate(
                name=f"Run {status.value}",
                experiment_id=experiment.id,
                status=status,
            )
            db_session.add(replicate)
            db_session.commit()
            assert replicate.status == status


class TestTodoModel:
    """Tests for Todo model."""

    def test_create_todo(self, db_session):
        """Should create a todo with required fields."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash="hash",
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

        assert todo.id is not None
        assert todo.status == TodoStatus.OPEN
        assert todo.priority == TodoPriority.MEDIUM

    def test_todo_with_assignment(self, db_session):
        """Should create a todo assigned to a user."""
        creator = User(
            email="creator@example.com",
            name="Creator",
            password_hash="hash",
        )
        assignee = User(
            email="assignee@example.com",
            name="Assignee",
            password_hash="hash",
        )
        db_session.add_all([creator, assignee])
        db_session.commit()

        todo = Todo(
            title="Assigned Todo",
            created_by=creator.id,
            assigned_to=assignee.id,
        )
        db_session.add(todo)
        db_session.commit()

        assert todo.assigned_to == assignee.id

    def test_todo_linked_to_project(self, db_session):
        """Should link todo to a project."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash="hash",
        )
        db_session.add(user)
        db_session.commit()

        project = Project(name="Test Project", created_by=user.id)
        db_session.add(project)
        db_session.commit()

        todo = Todo(
            title="Project Todo",
            created_by=user.id,
            project_id=project.id,
        )
        db_session.add(todo)
        db_session.commit()

        assert todo.project_id == project.id


class TestNoteModel:
    """Tests for Note model."""

    def test_create_note_on_experiment(self, db_session):
        """Should create a note attached to an experiment."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash="hash",
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
            content="# Test Note\n\nSome content",
            author_id=user.id,
            experiment_id=experiment.id,
        )
        db_session.add(note)
        db_session.commit()

        assert note.id is not None
        assert note.experiment_id == experiment.id
        assert note.replicate_id is None


class TestActivityLogModel:
    """Tests for ActivityLog model."""

    def test_create_activity_log(self, db_session):
        """Should create an activity log entry."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash="hash",
        )
        db_session.add(user)
        db_session.commit()

        activity = ActivityLog(
            user_id=user.id,
            action="created_project",
            entity_type="project",
            entity_id=uuid.uuid4(),
            metadata_json={"name": "Test Project"},
        )
        db_session.add(activity)
        db_session.commit()

        assert activity.id is not None
        assert activity.action == "created_project"
        assert activity.metadata_json["name"] == "Test Project"
