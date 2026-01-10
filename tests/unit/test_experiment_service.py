"""Unit tests for experiment service."""

import pytest

from app.models.user import User
from app.models.project import Project, ProjectStatus
from app.models.experiment import Experiment, ExperimentStatus
from app.services.experiment import ExperimentService
from app.services.password import hash_password


class TestExperimentServiceCreate:
    """Tests for experiment creation."""

    def test_create_experiment(self, db_session):
        """Should create a new experiment."""
        user = User(
            email="owner@example.com",
            name="Owner",
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

        service = ExperimentService(db_session)
        experiment = service.create_experiment(
            project=project,
            name="Test Experiment",
            created_by=user,
            description="A test experiment",
        )

        assert experiment.id is not None
        assert experiment.name == "Test Experiment"
        assert experiment.description == "A test experiment"
        assert experiment.status == ExperimentStatus.PLANNED
        assert experiment.project_id == project.id
        assert experiment.created_by == user.id

    def test_create_experiment_with_status(self, db_session):
        """Should create experiment with specified status."""
        user = User(
            email="owner@example.com",
            name="Owner",
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

        service = ExperimentService(db_session)
        experiment = service.create_experiment(
            project=project,
            name="Running Experiment",
            created_by=user,
            status=ExperimentStatus.RUNNING,
        )

        assert experiment.status == ExperimentStatus.RUNNING

    def test_create_experiment_trims_name(self, db_session):
        """Should trim whitespace from name."""
        user = User(
            email="owner@example.com",
            name="Owner",
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

        service = ExperimentService(db_session)
        experiment = service.create_experiment(
            project=project,
            name="  Test Experiment  ",
            created_by=user,
        )

        assert experiment.name == "Test Experiment"

    def test_create_experiment_duplicate_name_raises(self, db_session):
        """Should raise error for duplicate name within project."""
        user = User(
            email="owner@example.com",
            name="Owner",
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

        service = ExperimentService(db_session)
        service.create_experiment(project=project, name="Existing", created_by=user)

        with pytest.raises(ValueError, match="already exists"):
            service.create_experiment(project=project, name="Existing", created_by=user)

    def test_create_experiment_same_name_different_projects(self, db_session):
        """Should allow same name in different projects."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        project1 = Project(name="Project 1", created_by=user.id)
        project2 = Project(name="Project 2", created_by=user.id)
        db_session.add_all([project1, project2])
        db_session.commit()

        service = ExperimentService(db_session)
        exp1 = service.create_experiment(
            project=project1, name="Same Name", created_by=user
        )
        exp2 = service.create_experiment(
            project=project2, name="Same Name", created_by=user
        )

        assert exp1.name == exp2.name
        assert exp1.project_id != exp2.project_id


class TestExperimentServiceList:
    """Tests for listing experiments."""

    def test_list_experiments_by_project(self, db_session):
        """Should list experiments for a specific project."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        project1 = Project(name="Project 1", created_by=user.id)
        project2 = Project(name="Project 2", created_by=user.id)
        db_session.add_all([project1, project2])
        db_session.commit()

        service = ExperimentService(db_session)
        service.create_experiment(project=project1, name="Exp 1", created_by=user)
        service.create_experiment(project=project1, name="Exp 2", created_by=user)
        service.create_experiment(project=project2, name="Exp 3", created_by=user)

        experiments = service.list_experiments(project=project1)
        assert len(experiments) == 2
        assert all(e.project_id == project1.id for e in experiments)

    def test_list_experiments_excludes_archived(self, db_session):
        """Should exclude archived experiments by default."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        project = Project(name="Test Project", created_by=user.id)
        db_session.add(project)
        db_session.commit()

        service = ExperimentService(db_session)
        service.create_experiment(project=project, name="Active", created_by=user)
        service.create_experiment(
            project=project,
            name="Archived",
            created_by=user,
            status=ExperimentStatus.ARCHIVED,
        )

        experiments = service.list_experiments(project=project)
        assert len(experiments) == 1
        assert experiments[0].name == "Active"

    def test_list_experiments_include_archived(self, db_session):
        """Should include archived when requested."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        project = Project(name="Test Project", created_by=user.id)
        db_session.add(project)
        db_session.commit()

        service = ExperimentService(db_session)
        service.create_experiment(project=project, name="Active", created_by=user)
        service.create_experiment(
            project=project,
            name="Archived",
            created_by=user,
            status=ExperimentStatus.ARCHIVED,
        )

        experiments = service.list_experiments(project=project, include_archived=True)
        assert len(experiments) == 2

    def test_list_experiments_filter_by_status(self, db_session):
        """Should filter by status."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        project = Project(name="Test Project", created_by=user.id)
        db_session.add(project)
        db_session.commit()

        service = ExperimentService(db_session)
        service.create_experiment(project=project, name="Planned", created_by=user)
        service.create_experiment(
            project=project,
            name="Running",
            created_by=user,
            status=ExperimentStatus.RUNNING,
        )

        experiments = service.list_experiments(
            project=project, status_filter=ExperimentStatus.RUNNING
        )
        assert len(experiments) == 1
        assert experiments[0].name == "Running"

    def test_list_experiments_search(self, db_session):
        """Should search by name."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        project = Project(name="Test Project", created_by=user.id)
        db_session.add(project)
        db_session.commit()

        service = ExperimentService(db_session)
        service.create_experiment(project=project, name="Alpha Test", created_by=user)
        service.create_experiment(project=project, name="Beta Run", created_by=user)

        experiments = service.list_experiments(project=project, search="alpha")
        assert len(experiments) == 1
        assert experiments[0].name == "Alpha Test"


class TestExperimentServiceUpdate:
    """Tests for updating experiments."""

    def test_update_experiment_name(self, db_session):
        """Should update experiment name."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        project = Project(name="Test Project", created_by=user.id)
        db_session.add(project)
        db_session.commit()

        service = ExperimentService(db_session)
        experiment = service.create_experiment(
            project=project, name="Old Name", created_by=user
        )

        updated = service.update_experiment(experiment, name="New Name")
        assert updated.name == "New Name"

    def test_update_experiment_description(self, db_session):
        """Should update experiment description."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        project = Project(name="Test Project", created_by=user.id)
        db_session.add(project)
        db_session.commit()

        service = ExperimentService(db_session)
        experiment = service.create_experiment(
            project=project, name="Test", created_by=user
        )

        updated = service.update_experiment(experiment, description="New description")
        assert updated.description == "New description"

    def test_update_experiment_status(self, db_session):
        """Should update experiment status."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        project = Project(name="Test Project", created_by=user.id)
        db_session.add(project)
        db_session.commit()

        service = ExperimentService(db_session)
        experiment = service.create_experiment(
            project=project, name="Test", created_by=user
        )

        updated = service.update_experiment(experiment, status=ExperimentStatus.RUNNING)
        assert updated.status == ExperimentStatus.RUNNING

    def test_update_experiment_duplicate_name_raises(self, db_session):
        """Should raise error for duplicate name in same project."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        project = Project(name="Test Project", created_by=user.id)
        db_session.add(project)
        db_session.commit()

        service = ExperimentService(db_session)
        service.create_experiment(project=project, name="Existing", created_by=user)
        experiment = service.create_experiment(
            project=project, name="Test", created_by=user
        )

        with pytest.raises(ValueError, match="already exists"):
            service.update_experiment(experiment, name="Existing")


class TestExperimentServiceArchive:
    """Tests for archiving experiments."""

    def test_archive_experiment(self, db_session):
        """Should archive an experiment."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        project = Project(name="Test Project", created_by=user.id)
        db_session.add(project)
        db_session.commit()

        service = ExperimentService(db_session)
        experiment = service.create_experiment(
            project=project, name="Test", created_by=user
        )

        archived = service.archive_experiment(experiment)
        assert archived.status == ExperimentStatus.ARCHIVED


class TestExperimentServiceDelete:
    """Tests for deleting experiments."""

    def test_delete_experiment(self, db_session):
        """Should delete an experiment."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash=hash_password("password"),
        )
        db_session.add(user)
        db_session.commit()

        project = Project(name="Test Project", created_by=user.id)
        db_session.add(project)
        db_session.commit()

        service = ExperimentService(db_session)
        experiment = service.create_experiment(
            project=project, name="Test", created_by=user
        )
        experiment_id = experiment.id

        service.delete_experiment(experiment)

        deleted = service.get_by_id(experiment_id)
        assert deleted is None
