"""Unit tests for activity service."""

import pytest
from sqlalchemy.orm import Session

from app.models.activity import ActivityLog
from app.models.project import Project
from app.models.experiment import Experiment
from app.models.user import User
from app.services.activity import ActivityService
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


class TestActivityServiceLog:
    """Tests for logging activities."""

    def test_log_activity(self, db_session: Session, user: User, project: Project):
        """Should log an activity."""
        service = ActivityService(db_session)

        activity = service.log_activity(
            user=user,
            action="create",
            entity_type="project",
            entity_id=project.id,
        )

        assert activity.id is not None
        assert activity.user_id == user.id
        assert activity.action == "create"
        assert activity.entity_type == "project"
        assert activity.entity_id == project.id

    def test_log_activity_with_metadata(
        self, db_session: Session, user: User, project: Project
    ):
        """Should log activity with metadata."""
        service = ActivityService(db_session)

        activity = service.log_activity(
            user=user,
            action="update",
            entity_type="project",
            entity_id=project.id,
            metadata={"old_name": "Old Name", "new_name": "New Name"},
        )

        assert activity.metadata_json == {"old_name": "Old Name", "new_name": "New Name"}


class TestActivityServiceList:
    """Tests for listing activities."""

    def test_list_activities_by_entity(
        self, db_session: Session, user: User, project: Project
    ):
        """Should list activities for an entity."""
        service = ActivityService(db_session)

        service.log_activity(user, "create", "project", project.id)
        service.log_activity(user, "update", "project", project.id)

        activities = service.list_activities(
            entity_type="project",
            entity_id=project.id,
        )

        assert len(activities) == 2
        # Most recent first
        assert activities[0].action == "update"
        assert activities[1].action == "create"

    def test_list_activities_by_user(
        self, db_session: Session, user: User, project: Project
    ):
        """Should list activities by user."""
        service = ActivityService(db_session)

        service.log_activity(user, "create", "project", project.id)
        service.log_activity(user, "update", "project", project.id)

        activities = service.list_activities(user=user)

        assert len(activities) == 2

    def test_list_activities_limited(
        self, db_session: Session, user: User, project: Project
    ):
        """Should limit activities returned."""
        service = ActivityService(db_session)

        for i in range(5):
            service.log_activity(user, f"action_{i}", "project", project.id)

        activities = service.list_activities(
            entity_type="project",
            entity_id=project.id,
            limit=3,
        )

        assert len(activities) == 3


class TestActivityServiceRecent:
    """Tests for getting recent activities."""

    def test_get_recent_activities(
        self, db_session: Session, user: User, project: Project
    ):
        """Should get recent activities."""
        service = ActivityService(db_session)

        # Create another project
        project2 = Project(name="Test Project 2", created_by=user.id)
        db_session.add(project2)
        db_session.commit()

        service.log_activity(user, "create", "project", project.id)
        service.log_activity(user, "create", "project", project2.id)
        service.log_activity(user, "update", "project", project.id)

        recent = service.get_recent_activities(limit=10)

        assert len(recent) == 3
        # Most recent first
        assert recent[0].action == "update"

    def test_get_recent_activities_by_entity_type(
        self, db_session: Session, user: User, project: Project
    ):
        """Should filter recent activities by entity type."""
        service = ActivityService(db_session)

        experiment = Experiment(
            name="Test Experiment",
            project_id=project.id,
            created_by=user.id,
        )
        db_session.add(experiment)
        db_session.commit()

        service.log_activity(user, "create", "project", project.id)
        service.log_activity(user, "create", "experiment", experiment.id)

        recent = service.get_recent_activities(entity_type="experiment", limit=10)

        assert len(recent) == 1
        assert recent[0].entity_type == "experiment"
