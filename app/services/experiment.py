"""Experiment service for managing experiments within projects."""

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.experiment import Experiment, ExperimentStatus
from app.models.project import Project
from app.models.user import User


class ExperimentService:
    """Service for experiment management operations."""

    def __init__(self, db: Session):
        """Initialize with database session.

        Args:
            db: SQLAlchemy database session.
        """
        self.db = db

    def create_experiment(
        self,
        project: Project,
        name: str,
        created_by: User,
        description: Optional[str] = None,
        status: ExperimentStatus = ExperimentStatus.PLANNED,
    ) -> Experiment:
        """Create a new experiment within a project.

        Args:
            project: Project to create experiment in.
            name: Experiment name (unique within project).
            created_by: User creating the experiment.
            description: Experiment description.
            status: Initial experiment status.

        Returns:
            Created Experiment instance.

        Raises:
            ValueError: If experiment name already exists in project.
        """
        existing = self.get_by_name(project, name)
        if existing:
            raise ValueError(
                f"Experiment with name '{name}' already exists in this project"
            )

        experiment = Experiment(
            project_id=project.id,
            name=name.strip(),
            description=description.strip() if description else None,
            status=status,
            created_by=created_by.id,
        )
        self.db.add(experiment)
        self.db.commit()
        self.db.refresh(experiment)
        return experiment

    def get_by_id(self, experiment_id: uuid.UUID) -> Optional[Experiment]:
        """Get experiment by ID.

        Args:
            experiment_id: Experiment UUID.

        Returns:
            Experiment if found, None otherwise.
        """
        return self.db.get(Experiment, experiment_id)

    def get_by_name(self, project: Project, name: str) -> Optional[Experiment]:
        """Get experiment by name within a project.

        Args:
            project: Project to search in.
            name: Experiment name.

        Returns:
            Experiment if found, None otherwise.
        """
        stmt = select(Experiment).where(
            Experiment.project_id == project.id,
            Experiment.name == name.strip(),
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_experiments(
        self,
        project: Project,
        status_filter: Optional[ExperimentStatus] = None,
        include_archived: bool = False,
        search: Optional[str] = None,
    ) -> list[Experiment]:
        """List experiments for a project with optional filtering.

        Args:
            project: Project to list experiments for.
            status_filter: Filter by specific status.
            include_archived: Include archived experiments.
            search: Search by name (case-insensitive).

        Returns:
            List of Experiment instances.
        """
        stmt = (
            select(Experiment)
            .where(Experiment.project_id == project.id)
            .order_by(Experiment.updated_at.desc())
        )

        if status_filter:
            stmt = stmt.where(Experiment.status == status_filter)
        elif not include_archived:
            stmt = stmt.where(Experiment.status != ExperimentStatus.ARCHIVED)

        if search:
            stmt = stmt.where(Experiment.name.ilike(f"%{search}%"))

        return list(self.db.execute(stmt).scalars().all())

    def update_experiment(
        self,
        experiment: Experiment,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[ExperimentStatus] = None,
    ) -> Experiment:
        """Update experiment details.

        Args:
            experiment: Experiment instance to update.
            name: New name (optional).
            description: New description (optional).
            status: New status (optional).

        Returns:
            Updated Experiment instance.

        Raises:
            ValueError: If new name already exists in project.
        """
        if name is not None and name.strip() != experiment.name:
            existing = self.db.execute(
                select(Experiment).where(
                    Experiment.project_id == experiment.project_id,
                    Experiment.name == name.strip(),
                )
            ).scalar_one_or_none()
            if existing:
                raise ValueError(
                    f"Experiment with name '{name}' already exists in this project"
                )
            experiment.name = name.strip()

        if description is not None:
            experiment.description = description.strip() if description else None

        if status is not None:
            experiment.status = status

        self.db.commit()
        self.db.refresh(experiment)
        return experiment

    def archive_experiment(self, experiment: Experiment) -> Experiment:
        """Archive an experiment.

        Args:
            experiment: Experiment to archive.

        Returns:
            Archived Experiment instance.
        """
        experiment.status = ExperimentStatus.ARCHIVED
        self.db.commit()
        self.db.refresh(experiment)
        return experiment

    def delete_experiment(self, experiment: Experiment) -> None:
        """Delete an experiment.

        Args:
            experiment: Experiment to delete.
        """
        self.db.delete(experiment)
        self.db.commit()

    def get_experiment_stats(self, experiment: Experiment) -> dict:
        """Get statistics for an experiment.

        Args:
            experiment: Experiment to get stats for.

        Returns:
            Dictionary with experiment statistics.
        """
        from app.models.replicate import ReplicateStatus

        replicates = experiment.replicates
        replicate_counts = {}
        for status in ReplicateStatus:
            replicate_counts[status.value] = sum(
                1 for r in replicates if r.status == status
            )

        return {
            "replicate_count": len(replicates),
            "replicate_by_status": replicate_counts,
        }
