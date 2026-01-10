"""Experiment routes."""

import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.experiment import ExperimentStatus
from app.models.user import User
from app.services.activity import ActivityService
from app.services.experiment import ExperimentService
from app.services.note import NoteService
from app.services.project import ProjectService


router = APIRouter(prefix="/projects/{project_id}/experiments", tags=["experiments"])
templates = Jinja2Templates(directory="templates")


def get_project_or_redirect(project_id: str, db: Session):
    """Get project or return redirect response.

    Args:
        project_id: Project UUID string.
        db: Database session.

    Returns:
        Tuple of (project, None) or (None, redirect_response).
    """
    project_service = ProjectService(db)
    try:
        project = project_service.get_by_id(uuid.UUID(project_id))
    except ValueError:
        return None, RedirectResponse(
            url="/projects",
            status_code=status.HTTP_302_FOUND,
        )

    if not project:
        return None, RedirectResponse(
            url="/projects",
            status_code=status.HTTP_302_FOUND,
        )

    return project, None


@router.get("", response_class=HTMLResponse)
async def list_experiments(
    request: Request,
    project_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
    show_archived: bool = False,
):
    """List all experiments for a project.

    Args:
        request: FastAPI request.
        project_id: Project UUID.
        db: Database session.
        user: Current user.
        status_filter: Filter by status.
        search: Search by name.
        show_archived: Show archived experiments.

    Returns:
        Experiment list page.
    """
    project, redirect = get_project_or_redirect(project_id, db)
    if redirect:
        return redirect

    experiment_service = ExperimentService(db)

    parsed_status = None
    if status_filter and status_filter != "all":
        try:
            parsed_status = ExperimentStatus(status_filter)
        except ValueError:
            pass

    experiments = experiment_service.list_experiments(
        project=project,
        status_filter=parsed_status,
        include_archived=show_archived,
        search=search,
    )

    return templates.TemplateResponse(
        "experiments/list.html",
        {
            "request": request,
            "user": user,
            "project": project,
            "experiments": experiments,
            "status_filter": status_filter or "all",
            "search": search or "",
            "show_archived": show_archived,
            "statuses": ExperimentStatus,
        },
    )


@router.get("/new", response_class=HTMLResponse)
async def new_experiment_form(
    request: Request,
    project_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Show create experiment form.

    Args:
        request: FastAPI request.
        project_id: Project UUID.
        db: Database session.
        user: Current user.

    Returns:
        New experiment form page.
    """
    project, redirect = get_project_or_redirect(project_id, db)
    if redirect:
        return redirect

    return templates.TemplateResponse(
        "experiments/form.html",
        {
            "request": request,
            "user": user,
            "project": project,
            "experiment": None,
            "error": None,
            "statuses": ExperimentStatus,
        },
    )


@router.post("/new")
async def create_experiment(
    request: Request,
    project_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    name: Annotated[str, Form()],
    description: Annotated[str, Form()] = "",
    experiment_status: Annotated[str, Form()] = "planned",
):
    """Create a new experiment.

    Args:
        request: FastAPI request.
        project_id: Project UUID.
        db: Database session.
        user: Current user.
        name: Experiment name.
        description: Experiment description.
        experiment_status: Initial status.

    Returns:
        Redirect to experiment or form with error.
    """
    project, redirect = get_project_or_redirect(project_id, db)
    if redirect:
        return redirect

    experiment_service = ExperimentService(db)

    try:
        parsed_status = ExperimentStatus(experiment_status)
    except ValueError:
        parsed_status = ExperimentStatus.PLANNED

    try:
        experiment = experiment_service.create_experiment(
            project=project,
            name=name,
            created_by=user,
            description=description,
            status=parsed_status,
        )

        # Log activity
        activity_service = ActivityService(db)
        activity_service.log_activity(
            user=user,
            action="create",
            entity_type="experiment",
            entity_id=experiment.id,
            metadata={"name": experiment.name, "project_id": str(project.id)},
        )

        return RedirectResponse(
            url=f"/projects/{project.id}/experiments/{experiment.id}",
            status_code=status.HTTP_302_FOUND,
        )
    except ValueError as e:
        return templates.TemplateResponse(
            "experiments/form.html",
            {
                "request": request,
                "user": user,
                "project": project,
                "experiment": None,
                "error": str(e),
                "name": name,
                "description": description,
                "experiment_status": experiment_status,
                "statuses": ExperimentStatus,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@router.get("/{experiment_id}", response_class=HTMLResponse)
async def view_experiment(
    request: Request,
    project_id: str,
    experiment_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """View experiment details.

    Args:
        request: FastAPI request.
        project_id: Project UUID.
        experiment_id: Experiment UUID.
        db: Database session.
        user: Current user.

    Returns:
        Experiment detail page.
    """
    project, redirect = get_project_or_redirect(project_id, db)
    if redirect:
        return redirect

    experiment_service = ExperimentService(db)

    try:
        experiment = experiment_service.get_by_id(uuid.UUID(experiment_id))
    except ValueError:
        return RedirectResponse(
            url=f"/projects/{project.id}/experiments",
            status_code=status.HTTP_302_FOUND,
        )

    if not experiment or experiment.project_id != project.id:
        return RedirectResponse(
            url=f"/projects/{project.id}/experiments",
            status_code=status.HTTP_302_FOUND,
        )

    note_service = NoteService(db)
    stats = experiment_service.get_experiment_stats(experiment)
    notes = note_service.list_notes(experiment=experiment)

    return templates.TemplateResponse(
        "experiments/detail.html",
        {
            "request": request,
            "user": user,
            "project": project,
            "experiment": experiment,
            "stats": stats,
            "notes": notes,
        },
    )


@router.get("/{experiment_id}/edit", response_class=HTMLResponse)
async def edit_experiment_form(
    request: Request,
    project_id: str,
    experiment_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Show edit experiment form.

    Args:
        request: FastAPI request.
        project_id: Project UUID.
        experiment_id: Experiment UUID.
        db: Database session.
        user: Current user.

    Returns:
        Edit experiment form page.
    """
    project, redirect = get_project_or_redirect(project_id, db)
    if redirect:
        return redirect

    experiment_service = ExperimentService(db)

    try:
        experiment = experiment_service.get_by_id(uuid.UUID(experiment_id))
    except ValueError:
        return RedirectResponse(
            url=f"/projects/{project.id}/experiments",
            status_code=status.HTTP_302_FOUND,
        )

    if not experiment or experiment.project_id != project.id:
        return RedirectResponse(
            url=f"/projects/{project.id}/experiments",
            status_code=status.HTTP_302_FOUND,
        )

    return templates.TemplateResponse(
        "experiments/form.html",
        {
            "request": request,
            "user": user,
            "project": project,
            "experiment": experiment,
            "error": None,
            "statuses": ExperimentStatus,
        },
    )


@router.post("/{experiment_id}/edit")
async def update_experiment(
    request: Request,
    project_id: str,
    experiment_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    name: Annotated[str, Form()],
    description: Annotated[str, Form()] = "",
    experiment_status: Annotated[str, Form()] = "planned",
):
    """Update an experiment.

    Args:
        request: FastAPI request.
        project_id: Project UUID.
        experiment_id: Experiment UUID.
        db: Database session.
        user: Current user.
        name: Experiment name.
        description: Experiment description.
        experiment_status: Experiment status.

    Returns:
        Redirect to experiment or form with error.
    """
    project, redirect = get_project_or_redirect(project_id, db)
    if redirect:
        return redirect

    experiment_service = ExperimentService(db)

    try:
        experiment = experiment_service.get_by_id(uuid.UUID(experiment_id))
    except ValueError:
        return RedirectResponse(
            url=f"/projects/{project.id}/experiments",
            status_code=status.HTTP_302_FOUND,
        )

    if not experiment or experiment.project_id != project.id:
        return RedirectResponse(
            url=f"/projects/{project.id}/experiments",
            status_code=status.HTTP_302_FOUND,
        )

    try:
        parsed_status = ExperimentStatus(experiment_status)
    except ValueError:
        parsed_status = experiment.status

    try:
        experiment_service.update_experiment(
            experiment=experiment,
            name=name,
            description=description,
            status=parsed_status,
        )

        # Log activity
        activity_service = ActivityService(db)
        activity_service.log_activity(
            user=user,
            action="update",
            entity_type="experiment",
            entity_id=experiment.id,
            metadata={"name": experiment.name},
        )

        return RedirectResponse(
            url=f"/projects/{project.id}/experiments/{experiment.id}",
            status_code=status.HTTP_302_FOUND,
        )
    except ValueError as e:
        return templates.TemplateResponse(
            "experiments/form.html",
            {
                "request": request,
                "user": user,
                "project": project,
                "experiment": experiment,
                "error": str(e),
                "name": name,
                "description": description,
                "experiment_status": experiment_status,
                "statuses": ExperimentStatus,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@router.post("/{experiment_id}/archive")
async def archive_experiment(
    project_id: str,
    experiment_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Archive an experiment.

    Args:
        project_id: Project UUID.
        experiment_id: Experiment UUID.
        db: Database session.
        user: Current user.

    Returns:
        Redirect to experiments list.
    """
    project, redirect = get_project_or_redirect(project_id, db)
    if redirect:
        return redirect

    experiment_service = ExperimentService(db)

    try:
        experiment = experiment_service.get_by_id(uuid.UUID(experiment_id))
    except ValueError:
        return RedirectResponse(
            url=f"/projects/{project.id}/experiments",
            status_code=status.HTTP_302_FOUND,
        )

    if experiment and experiment.project_id == project.id:
        experiment_service.archive_experiment(experiment)

        # Log activity
        activity_service = ActivityService(db)
        activity_service.log_activity(
            user=user,
            action="archive",
            entity_type="experiment",
            entity_id=experiment.id,
            metadata={"name": experiment.name},
        )

    return RedirectResponse(
        url=f"/projects/{project.id}/experiments",
        status_code=status.HTTP_302_FOUND,
    )


@router.post("/{experiment_id}/delete")
async def delete_experiment(
    project_id: str,
    experiment_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Delete an experiment.

    Args:
        project_id: Project UUID.
        experiment_id: Experiment UUID.
        db: Database session.
        user: Current user.

    Returns:
        Redirect to experiments list.
    """
    project, redirect = get_project_or_redirect(project_id, db)
    if redirect:
        return redirect

    experiment_service = ExperimentService(db)

    try:
        experiment = experiment_service.get_by_id(uuid.UUID(experiment_id))
    except ValueError:
        return RedirectResponse(
            url=f"/projects/{project.id}/experiments",
            status_code=status.HTTP_302_FOUND,
        )

    if experiment and experiment.project_id == project.id:
        # Capture experiment info before deletion
        experiment_id = experiment.id
        experiment_name = experiment.name

        experiment_service.delete_experiment(experiment)

        # Log activity
        activity_service = ActivityService(db)
        activity_service.log_activity(
            user=user,
            action="delete",
            entity_type="experiment",
            entity_id=experiment_id,
            metadata={"name": experiment_name},
        )

    return RedirectResponse(
        url=f"/projects/{project.id}/experiments",
        status_code=status.HTTP_302_FOUND,
    )
