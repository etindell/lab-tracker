"""Project service for managing research projects."""

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectStatus
from app.models.user import User


class ProjectService:
    """Service for project management operations."""

    def __init__(self, db: Session):
        """Initialize with database session.

        Args:
            db: SQLAlchemy database session.
        """
        self.db = db

    def create_project(
        self,
        name: str,
        created_by: User,
        description: Optional[str] = None,
        status: ProjectStatus = ProjectStatus.ACTIVE,
    ) -> Project:
        """Create a new project.

        Args:
            name: Project name (unique).
            created_by: User creating the project.
            description: Project description.
            status: Initial project status.

        Returns:
            Created Project instance.

        Raises:
            ValueError: If project name already exists.
        """
        # Check for existing name
        existing = self.get_by_name(name)
        if existing:
            raise ValueError(f"Project with name '{name}' already exists")

        project = Project(
            name=name.strip(),
            description=description.strip() if description else None,
            status=status,
            created_by=created_by.id,
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_by_id(self, project_id: uuid.UUID) -> Optional[Project]:
        """Get project by ID.

        Args:
            project_id: Project UUID.

        Returns:
            Project if found, None otherwise.
        """
        return self.db.get(Project, project_id)

    def get_by_name(self, name: str) -> Optional[Project]:
        """Get project by name.

        Args:
            name: Project name.

        Returns:
            Project if found, None otherwise.
        """
        stmt = select(Project).where(Project.name == name.strip())
        return self.db.execute(stmt).scalar_one_or_none()

    def list_projects(
        self,
        status_filter: Optional[ProjectStatus] = None,
        include_archived: bool = False,
        search: Optional[str] = None,
    ) -> list[Project]:
        """List projects with optional filtering.

        Args:
            status_filter: Filter by specific status.
            include_archived: Include archived projects.
            search: Search by name (case-insensitive).

        Returns:
            List of Project instances.
        """
        stmt = select(Project).order_by(Project.updated_at.desc())

        if status_filter:
            stmt = stmt.where(Project.status == status_filter)
        elif not include_archived:
            stmt = stmt.where(Project.status != ProjectStatus.ARCHIVED)

        if search:
            stmt = stmt.where(Project.name.ilike(f"%{search}%"))

        return list(self.db.execute(stmt).scalars().all())

    def update_project(
        self,
        project: Project,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[ProjectStatus] = None,
    ) -> Project:
        """Update project details.

        Args:
            project: Project instance to update.
            name: New name (optional).
            description: New description (optional).
            status: New status (optional).

        Returns:
            Updated Project instance.

        Raises:
            ValueError: If new name already exists.
        """
        if name is not None and name.strip() != project.name:
            existing = self.get_by_name(name)
            if existing:
                raise ValueError(f"Project with name '{name}' already exists")
            project.name = name.strip()

        if description is not None:
            project.description = description.strip() if description else None

        if status is not None:
            project.status = status

        self.db.commit()
        self.db.refresh(project)
        return project

    def archive_project(self, project: Project) -> Project:
        """Archive a project.

        Args:
            project: Project to archive.

        Returns:
            Archived Project instance.
        """
        project.status = ProjectStatus.ARCHIVED
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_project_stats(self, project: Project) -> dict:
        """Get statistics for a project.

        Args:
            project: Project to get stats for.

        Returns:
            Dictionary with project statistics.
        """
        from app.models.experiment import ExperimentStatus

        experiments = project.experiments
        experiment_counts = {}
        for status in ExperimentStatus:
            experiment_counts[status.value] = sum(
                1 for e in experiments if e.status == status
            )

        total_replicates = 0
        replicate_counts = {}
        for exp in experiments:
            total_replicates += len(exp.replicates)
            for rep in exp.replicates:
                status = rep.status.value
                replicate_counts[status] = replicate_counts.get(status, 0) + 1

        return {
            "experiment_count": len(experiments),
            "experiment_by_status": experiment_counts,
            "replicate_count": total_replicates,
            "replicate_by_status": replicate_counts,
        }
