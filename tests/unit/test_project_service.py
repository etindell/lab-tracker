"""Unit tests for project service."""

import pytest

from app.models.user import User
from app.models.project import Project, ProjectStatus
from app.services.project import ProjectService
from app.services.password import hash_password


class TestProjectServiceCreate:
    """Tests for project creation."""

    def test_create_project(self, db_session):
        """Should create a new project."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        service = ProjectService(db_session)
        project = service.create_project(
            name="Test Project",
            created_by=user,
            description="A test project",
        )

        assert project.id is not None
        assert project.name == "Test Project"
        assert project.description == "A test project"
        assert project.status == ProjectStatus.ACTIVE
        assert project.created_by == user.id

    def test_create_project_with_status(self, db_session):
        """Should create project with specified status."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        service = ProjectService(db_session)
        project = service.create_project(
            name="On Hold Project",
            created_by=user,
            status=ProjectStatus.ON_HOLD,
        )

        assert project.status == ProjectStatus.ON_HOLD

    def test_create_project_trims_name(self, db_session):
        """Should trim whitespace from name."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        service = ProjectService(db_session)
        project = service.create_project(
            name="  Test Project  ",
            created_by=user,
        )

        assert project.name == "Test Project"

    def test_create_project_duplicate_name_raises(self, db_session):
        """Should raise error for duplicate name."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        service = ProjectService(db_session)
        service.create_project(name="Existing", created_by=user)

        with pytest.raises(ValueError, match="already exists"):
            service.create_project(name="Existing", created_by=user)


class TestProjectServiceList:
    """Tests for listing projects."""

    def test_list_projects(self, db_session):
        """Should list all non-archived projects."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        service = ProjectService(db_session)
        service.create_project(name="Project 1", created_by=user)
        service.create_project(name="Project 2", created_by=user)

        projects = service.list_projects()
        assert len(projects) == 2

    def test_list_projects_excludes_archived(self, db_session):
        """Should exclude archived projects by default."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        service = ProjectService(db_session)
        service.create_project(name="Active Project", created_by=user)
        archived = service.create_project(
            name="Archived Project",
            created_by=user,
            status=ProjectStatus.ARCHIVED,
        )

        projects = service.list_projects()
        assert len(projects) == 1
        assert projects[0].name == "Active Project"

    def test_list_projects_include_archived(self, db_session):
        """Should include archived when requested."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        service = ProjectService(db_session)
        service.create_project(name="Active Project", created_by=user)
        service.create_project(
            name="Archived Project",
            created_by=user,
            status=ProjectStatus.ARCHIVED,
        )

        projects = service.list_projects(include_archived=True)
        assert len(projects) == 2

    def test_list_projects_filter_by_status(self, db_session):
        """Should filter by status."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        service = ProjectService(db_session)
        service.create_project(name="Active", created_by=user)
        service.create_project(
            name="On Hold",
            created_by=user,
            status=ProjectStatus.ON_HOLD,
        )

        projects = service.list_projects(status_filter=ProjectStatus.ON_HOLD)
        assert len(projects) == 1
        assert projects[0].name == "On Hold"

    def test_list_projects_search(self, db_session):
        """Should search by name."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        service = ProjectService(db_session)
        service.create_project(name="Alpha Project", created_by=user)
        service.create_project(name="Beta Test", created_by=user)

        projects = service.list_projects(search="alpha")
        assert len(projects) == 1
        assert projects[0].name == "Alpha Project"


class TestProjectServiceUpdate:
    """Tests for updating projects."""

    def test_update_project_name(self, db_session):
        """Should update project name."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        service = ProjectService(db_session)
        project = service.create_project(name="Old Name", created_by=user)

        updated = service.update_project(project, name="New Name")
        assert updated.name == "New Name"

    def test_update_project_description(self, db_session):
        """Should update project description."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        service = ProjectService(db_session)
        project = service.create_project(name="Test", created_by=user)

        updated = service.update_project(project, description="New description")
        assert updated.description == "New description"

    def test_update_project_status(self, db_session):
        """Should update project status."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        service = ProjectService(db_session)
        project = service.create_project(name="Test", created_by=user)

        updated = service.update_project(project, status=ProjectStatus.COMPLETE)
        assert updated.status == ProjectStatus.COMPLETE

    def test_update_project_duplicate_name_raises(self, db_session):
        """Should raise error for duplicate name."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        service = ProjectService(db_session)
        service.create_project(name="Existing", created_by=user)
        project = service.create_project(name="Test", created_by=user)

        with pytest.raises(ValueError, match="already exists"):
            service.update_project(project, name="Existing")


class TestProjectServiceArchive:
    """Tests for archiving projects."""

    def test_archive_project(self, db_session):
        """Should archive a project."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        service = ProjectService(db_session)
        project = service.create_project(name="Test", created_by=user)

        archived = service.archive_project(project)
        assert archived.status == ProjectStatus.ARCHIVED
