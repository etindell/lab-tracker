"""Unit tests for replicate service."""

import pytest

from app.models.user import User
from app.models.project import Project
from app.models.experiment import Experiment
from app.models.replicate import Replicate, ReplicateStatus
from app.services.replicate import ReplicateService
from app.services.password import hash_password


class TestReplicateServiceCreate:
    """Tests for replicate creation."""

    def test_create_replicate(self, db_session):
        """Should create a new replicate."""
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

        experiment = Experiment(
            name="Test Experiment",
            project_id=project.id,
            created_by=user.id,
        )
        db_session.add(experiment)
        db_session.commit()

        service = ReplicateService(db_session)
        replicate = service.create_replicate(
            experiment=experiment,
            name="Replicate 1",
            summary="First replicate",
        )

        assert replicate.id is not None
        assert replicate.name == "Replicate 1"
        assert replicate.summary == "First replicate"
        assert replicate.status == ReplicateStatus.PLANNED
        assert replicate.experiment_id == experiment.id

    def test_create_replicate_with_status(self, db_session):
        """Should create replicate with specified status."""
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

        experiment = Experiment(
            name="Test Experiment",
            project_id=project.id,
            created_by=user.id,
        )
        db_session.add(experiment)
        db_session.commit()

        service = ReplicateService(db_session)
        replicate = service.create_replicate(
            experiment=experiment,
            name="Replicate 1",
            status=ReplicateStatus.IN_PROGRESS,
        )

        assert replicate.status == ReplicateStatus.IN_PROGRESS

    def test_create_replicate_with_performer(self, db_session):
        """Should create replicate with performer assigned."""
        user = User(
            email="owner@example.com",
            name="Owner",
            password_hash=hash_password("password"),
        )
        performer = User(
            email="performer@example.com",
            name="Performer",
            password_hash=hash_password("password"),
        )
        db_session.add_all([user, performer])
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

        service = ReplicateService(db_session)
        replicate = service.create_replicate(
            experiment=experiment,
            name="Replicate 1",
            performed_by=performer,
        )

        assert replicate.performed_by == performer.id

    def test_create_replicate_trims_name(self, db_session):
        """Should trim whitespace from name."""
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

        experiment = Experiment(
            name="Test Experiment",
            project_id=project.id,
            created_by=user.id,
        )
        db_session.add(experiment)
        db_session.commit()

        service = ReplicateService(db_session)
        replicate = service.create_replicate(
            experiment=experiment,
            name="  Replicate 1  ",
        )

        assert replicate.name == "Replicate 1"


class TestReplicateServiceList:
    """Tests for listing replicates."""

    def test_list_replicates_by_experiment(self, db_session):
        """Should list replicates for a specific experiment."""
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

        exp1 = Experiment(name="Exp 1", project_id=project.id, created_by=user.id)
        exp2 = Experiment(name="Exp 2", project_id=project.id, created_by=user.id)
        db_session.add_all([exp1, exp2])
        db_session.commit()

        service = ReplicateService(db_session)
        service.create_replicate(experiment=exp1, name="Rep 1")
        service.create_replicate(experiment=exp1, name="Rep 2")
        service.create_replicate(experiment=exp2, name="Rep 3")

        replicates = service.list_replicates(experiment=exp1)
        assert len(replicates) == 2
        assert all(r.experiment_id == exp1.id for r in replicates)

    def test_list_replicates_filter_by_status(self, db_session):
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

        experiment = Experiment(
            name="Test Experiment",
            project_id=project.id,
            created_by=user.id,
        )
        db_session.add(experiment)
        db_session.commit()

        service = ReplicateService(db_session)
        service.create_replicate(experiment=experiment, name="Rep 1")
        service.create_replicate(
            experiment=experiment,
            name="Rep 2",
            status=ReplicateStatus.IN_PROGRESS,
        )

        replicates = service.list_replicates(
            experiment=experiment, status_filter=ReplicateStatus.IN_PROGRESS
        )
        assert len(replicates) == 1
        assert replicates[0].name == "Rep 2"

    def test_list_replicates_search(self, db_session):
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

        experiment = Experiment(
            name="Test Experiment",
            project_id=project.id,
            created_by=user.id,
        )
        db_session.add(experiment)
        db_session.commit()

        service = ReplicateService(db_session)
        service.create_replicate(experiment=experiment, name="Alpha Run")
        service.create_replicate(experiment=experiment, name="Beta Test")

        replicates = service.list_replicates(experiment=experiment, search="alpha")
        assert len(replicates) == 1
        assert replicates[0].name == "Alpha Run"


class TestReplicateServiceUpdate:
    """Tests for updating replicates."""

    def test_update_replicate_name(self, db_session):
        """Should update replicate name."""
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

        experiment = Experiment(
            name="Test Experiment",
            project_id=project.id,
            created_by=user.id,
        )
        db_session.add(experiment)
        db_session.commit()

        service = ReplicateService(db_session)
        replicate = service.create_replicate(experiment=experiment, name="Old Name")

        updated = service.update_replicate(replicate, name="New Name")
        assert updated.name == "New Name"

    def test_update_replicate_status(self, db_session):
        """Should update replicate status."""
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

        experiment = Experiment(
            name="Test Experiment",
            project_id=project.id,
            created_by=user.id,
        )
        db_session.add(experiment)
        db_session.commit()

        service = ReplicateService(db_session)
        replicate = service.create_replicate(experiment=experiment, name="Test")

        updated = service.update_replicate(replicate, status=ReplicateStatus.DONE)
        assert updated.status == ReplicateStatus.DONE

    def test_update_replicate_summary(self, db_session):
        """Should update replicate summary."""
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

        experiment = Experiment(
            name="Test Experiment",
            project_id=project.id,
            created_by=user.id,
        )
        db_session.add(experiment)
        db_session.commit()

        service = ReplicateService(db_session)
        replicate = service.create_replicate(experiment=experiment, name="Test")

        updated = service.update_replicate(replicate, summary="New summary")
        assert updated.summary == "New summary"

    def test_update_replicate_results_link(self, db_session):
        """Should update replicate results link."""
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

        experiment = Experiment(
            name="Test Experiment",
            project_id=project.id,
            created_by=user.id,
        )
        db_session.add(experiment)
        db_session.commit()

        service = ReplicateService(db_session)
        replicate = service.create_replicate(experiment=experiment, name="Test")

        updated = service.update_replicate(
            replicate, results_link="https://example.com/results"
        )
        assert updated.results_link == "https://example.com/results"


class TestReplicateServiceDelete:
    """Tests for deleting replicates."""

    def test_delete_replicate(self, db_session):
        """Should delete a replicate."""
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

        experiment = Experiment(
            name="Test Experiment",
            project_id=project.id,
            created_by=user.id,
        )
        db_session.add(experiment)
        db_session.commit()

        service = ReplicateService(db_session)
        replicate = service.create_replicate(experiment=experiment, name="Test")
        replicate_id = replicate.id

        service.delete_replicate(replicate)

        deleted = service.get_by_id(replicate_id)
        assert deleted is None


class TestReplicateServiceStatusChange:
    """Tests for inline status change."""

    def test_change_status(self, db_session):
        """Should change replicate status."""
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

        experiment = Experiment(
            name="Test Experiment",
            project_id=project.id,
            created_by=user.id,
        )
        db_session.add(experiment)
        db_session.commit()

        service = ReplicateService(db_session)
        replicate = service.create_replicate(experiment=experiment, name="Test")

        updated = service.change_status(replicate, ReplicateStatus.IN_PROGRESS)
        assert updated.status == ReplicateStatus.IN_PROGRESS

    def test_change_status_to_blocked(self, db_session):
        """Should change status to blocked."""
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

        experiment = Experiment(
            name="Test Experiment",
            project_id=project.id,
            created_by=user.id,
        )
        db_session.add(experiment)
        db_session.commit()

        service = ReplicateService(db_session)
        replicate = service.create_replicate(
            experiment=experiment,
            name="Test",
            status=ReplicateStatus.IN_PROGRESS,
        )

        updated = service.change_status(replicate, ReplicateStatus.BLOCKED)
        assert updated.status == ReplicateStatus.BLOCKED
