"""Replicate routes."""

import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.replicate import ReplicateStatus
from app.models.user import User
from app.services.experiment import ExperimentService
from app.services.note import NoteService
from app.services.project import ProjectService
from app.services.replicate import ReplicateService
from app.services.user import UserService


router = APIRouter(
    prefix="/projects/{project_id}/experiments/{experiment_id}/replicates",
    tags=["replicates"],
)
templates = Jinja2Templates(directory="templates")


def get_project_and_experiment_or_redirect(
    project_id: str, experiment_id: str, db: Session
):
    """Get project and experiment or return redirect response.

    Args:
        project_id: Project UUID string.
        experiment_id: Experiment UUID string.
        db: Database session.

    Returns:
        Tuple of (project, experiment, None) or (None, None, redirect_response).
    """
    project_service = ProjectService(db)
    experiment_service = ExperimentService(db)

    try:
        project = project_service.get_by_id(uuid.UUID(project_id))
    except ValueError:
        return None, None, RedirectResponse(
            url="/projects",
            status_code=status.HTTP_302_FOUND,
        )

    if not project:
        return None, None, RedirectResponse(
            url="/projects",
            status_code=status.HTTP_302_FOUND,
        )

    try:
        experiment = experiment_service.get_by_id(uuid.UUID(experiment_id))
    except ValueError:
        return None, None, RedirectResponse(
            url=f"/projects/{project.id}/experiments",
            status_code=status.HTTP_302_FOUND,
        )

    if not experiment or experiment.project_id != project.id:
        return None, None, RedirectResponse(
            url=f"/projects/{project.id}/experiments",
            status_code=status.HTTP_302_FOUND,
        )

    return project, experiment, None


@router.get("", response_class=HTMLResponse)
async def list_replicates(
    request: Request,
    project_id: str,
    experiment_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
):
    """List all replicates for an experiment.

    Args:
        request: FastAPI request.
        project_id: Project UUID.
        experiment_id: Experiment UUID.
        db: Database session.
        user: Current user.
        status_filter: Filter by status.
        search: Search by name.

    Returns:
        Replicate list page.
    """
    project, experiment, redirect = get_project_and_experiment_or_redirect(
        project_id, experiment_id, db
    )
    if redirect:
        return redirect

    replicate_service = ReplicateService(db)

    parsed_status = None
    if status_filter and status_filter != "all":
        try:
            parsed_status = ReplicateStatus(status_filter)
        except ValueError:
            pass

    replicates = replicate_service.list_replicates(
        experiment=experiment,
        status_filter=parsed_status,
        search=search,
    )

    return templates.TemplateResponse(
        "replicates/list.html",
        {
            "request": request,
            "user": user,
            "project": project,
            "experiment": experiment,
            "replicates": replicates,
            "status_filter": status_filter or "all",
            "search": search or "",
            "statuses": ReplicateStatus,
        },
    )


@router.get("/new", response_class=HTMLResponse)
async def new_replicate_form(
    request: Request,
    project_id: str,
    experiment_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Show create replicate form.

    Args:
        request: FastAPI request.
        project_id: Project UUID.
        experiment_id: Experiment UUID.
        db: Database session.
        user: Current user.

    Returns:
        New replicate form page.
    """
    project, experiment, redirect = get_project_and_experiment_or_redirect(
        project_id, experiment_id, db
    )
    if redirect:
        return redirect

    user_service = UserService(db)
    users = user_service.list_users()

    return templates.TemplateResponse(
        "replicates/form.html",
        {
            "request": request,
            "user": user,
            "project": project,
            "experiment": experiment,
            "replicate": None,
            "error": None,
            "statuses": ReplicateStatus,
            "users": users,
        },
    )


@router.post("/new")
async def create_replicate(
    request: Request,
    project_id: str,
    experiment_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    name: Annotated[str, Form()],
    summary: Annotated[str, Form()] = "",
    replicate_status: Annotated[str, Form()] = "planned",
    performed_by_id: Annotated[str, Form()] = "",
    results_link: Annotated[str, Form()] = "",
    notes_text: Annotated[str, Form()] = "",
):
    """Create a new replicate.

    Args:
        request: FastAPI request.
        project_id: Project UUID.
        experiment_id: Experiment UUID.
        db: Database session.
        user: Current user.
        name: Replicate name.
        summary: Replicate summary.
        replicate_status: Initial status.
        performed_by_id: Performer user ID.
        results_link: Link to results.
        notes_text: Additional notes.

    Returns:
        Redirect to replicate or form with error.
    """
    project, experiment, redirect = get_project_and_experiment_or_redirect(
        project_id, experiment_id, db
    )
    if redirect:
        return redirect

    replicate_service = ReplicateService(db)
    user_service = UserService(db)

    try:
        parsed_status = ReplicateStatus(replicate_status)
    except ValueError:
        parsed_status = ReplicateStatus.PLANNED

    performer = None
    if performed_by_id:
        try:
            performer = user_service.get_by_id(uuid.UUID(performed_by_id))
        except ValueError:
            pass

    replicate = replicate_service.create_replicate(
        experiment=experiment,
        name=name,
        summary=summary,
        status=parsed_status,
        performed_by=performer,
        results_link=results_link,
        notes_text=notes_text,
    )

    return RedirectResponse(
        url=f"/projects/{project.id}/experiments/{experiment.id}/replicates/{replicate.id}",
        status_code=status.HTTP_302_FOUND,
    )


@router.get("/{replicate_id}", response_class=HTMLResponse)
async def view_replicate(
    request: Request,
    project_id: str,
    experiment_id: str,
    replicate_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """View replicate details.

    Args:
        request: FastAPI request.
        project_id: Project UUID.
        experiment_id: Experiment UUID.
        replicate_id: Replicate UUID.
        db: Database session.
        user: Current user.

    Returns:
        Replicate detail page.
    """
    project, experiment, redirect = get_project_and_experiment_or_redirect(
        project_id, experiment_id, db
    )
    if redirect:
        return redirect

    replicate_service = ReplicateService(db)

    try:
        replicate = replicate_service.get_by_id(uuid.UUID(replicate_id))
    except ValueError:
        return RedirectResponse(
            url=f"/projects/{project.id}/experiments/{experiment.id}/replicates",
            status_code=status.HTTP_302_FOUND,
        )

    if not replicate or replicate.experiment_id != experiment.id:
        return RedirectResponse(
            url=f"/projects/{project.id}/experiments/{experiment.id}/replicates",
            status_code=status.HTTP_302_FOUND,
        )

    note_service = NoteService(db)
    notes = note_service.list_notes(replicate=replicate)

    return templates.TemplateResponse(
        "replicates/detail.html",
        {
            "request": request,
            "user": user,
            "project": project,
            "experiment": experiment,
            "replicate": replicate,
            "notes": notes,
            "statuses": ReplicateStatus,
        },
    )


@router.get("/{replicate_id}/edit", response_class=HTMLResponse)
async def edit_replicate_form(
    request: Request,
    project_id: str,
    experiment_id: str,
    replicate_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Show edit replicate form.

    Args:
        request: FastAPI request.
        project_id: Project UUID.
        experiment_id: Experiment UUID.
        replicate_id: Replicate UUID.
        db: Database session.
        user: Current user.

    Returns:
        Edit replicate form page.
    """
    project, experiment, redirect = get_project_and_experiment_or_redirect(
        project_id, experiment_id, db
    )
    if redirect:
        return redirect

    replicate_service = ReplicateService(db)
    user_service = UserService(db)

    try:
        replicate = replicate_service.get_by_id(uuid.UUID(replicate_id))
    except ValueError:
        return RedirectResponse(
            url=f"/projects/{project.id}/experiments/{experiment.id}/replicates",
            status_code=status.HTTP_302_FOUND,
        )

    if not replicate or replicate.experiment_id != experiment.id:
        return RedirectResponse(
            url=f"/projects/{project.id}/experiments/{experiment.id}/replicates",
            status_code=status.HTTP_302_FOUND,
        )

    users = user_service.list_users()

    return templates.TemplateResponse(
        "replicates/form.html",
        {
            "request": request,
            "user": user,
            "project": project,
            "experiment": experiment,
            "replicate": replicate,
            "error": None,
            "statuses": ReplicateStatus,
            "users": users,
        },
    )


@router.post("/{replicate_id}/edit")
async def update_replicate(
    request: Request,
    project_id: str,
    experiment_id: str,
    replicate_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    name: Annotated[str, Form()],
    summary: Annotated[str, Form()] = "",
    replicate_status: Annotated[str, Form()] = "planned",
    performed_by_id: Annotated[str, Form()] = "",
    results_link: Annotated[str, Form()] = "",
    notes_text: Annotated[str, Form()] = "",
):
    """Update a replicate.

    Args:
        request: FastAPI request.
        project_id: Project UUID.
        experiment_id: Experiment UUID.
        replicate_id: Replicate UUID.
        db: Database session.
        user: Current user.
        name: Replicate name.
        summary: Replicate summary.
        replicate_status: Replicate status.
        performed_by_id: Performer user ID.
        results_link: Link to results.
        notes_text: Additional notes.

    Returns:
        Redirect to replicate or form with error.
    """
    project, experiment, redirect = get_project_and_experiment_or_redirect(
        project_id, experiment_id, db
    )
    if redirect:
        return redirect

    replicate_service = ReplicateService(db)
    user_service = UserService(db)

    try:
        replicate = replicate_service.get_by_id(uuid.UUID(replicate_id))
    except ValueError:
        return RedirectResponse(
            url=f"/projects/{project.id}/experiments/{experiment.id}/replicates",
            status_code=status.HTTP_302_FOUND,
        )

    if not replicate or replicate.experiment_id != experiment.id:
        return RedirectResponse(
            url=f"/projects/{project.id}/experiments/{experiment.id}/replicates",
            status_code=status.HTTP_302_FOUND,
        )

    try:
        parsed_status = ReplicateStatus(replicate_status)
    except ValueError:
        parsed_status = replicate.status

    performer = None
    clear_performer = False
    if performed_by_id:
        try:
            performer = user_service.get_by_id(uuid.UUID(performed_by_id))
        except ValueError:
            pass
    else:
        clear_performer = True

    replicate_service.update_replicate(
        replicate=replicate,
        name=name,
        summary=summary,
        status=parsed_status,
        performed_by=performer,
        results_link=results_link,
        notes_text=notes_text,
        clear_performer=clear_performer,
    )

    return RedirectResponse(
        url=f"/projects/{project.id}/experiments/{experiment.id}/replicates/{replicate.id}",
        status_code=status.HTTP_302_FOUND,
    )


@router.post("/{replicate_id}/status")
async def change_replicate_status(
    request: Request,
    project_id: str,
    experiment_id: str,
    replicate_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    status_value: Annotated[str, Form(alias="status")],
):
    """Change replicate status (inline update for HTMX).

    Args:
        request: FastAPI request.
        project_id: Project UUID.
        experiment_id: Experiment UUID.
        replicate_id: Replicate UUID.
        db: Database session.
        user: Current user.
        status_value: New status value.

    Returns:
        Status badge HTML fragment.
    """
    project, experiment, redirect = get_project_and_experiment_or_redirect(
        project_id, experiment_id, db
    )
    if redirect:
        return redirect

    replicate_service = ReplicateService(db)

    try:
        replicate = replicate_service.get_by_id(uuid.UUID(replicate_id))
    except ValueError:
        return HTMLResponse(content="Invalid replicate", status_code=400)

    if not replicate or replicate.experiment_id != experiment.id:
        return HTMLResponse(content="Replicate not found", status_code=404)

    try:
        new_status = ReplicateStatus(status_value)
    except ValueError:
        return HTMLResponse(content="Invalid status", status_code=400)

    replicate_service.change_status(replicate, new_status)

    return templates.TemplateResponse(
        "replicates/_status_badge.html",
        {
            "request": request,
            "replicate": replicate,
            "project": project,
            "experiment": experiment,
            "statuses": ReplicateStatus,
        },
    )


@router.post("/{replicate_id}/delete")
async def delete_replicate(
    project_id: str,
    experiment_id: str,
    replicate_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Delete a replicate.

    Args:
        project_id: Project UUID.
        experiment_id: Experiment UUID.
        replicate_id: Replicate UUID.
        db: Database session.
        user: Current user.

    Returns:
        Redirect to replicates list.
    """
    project, experiment, redirect = get_project_and_experiment_or_redirect(
        project_id, experiment_id, db
    )
    if redirect:
        return redirect

    replicate_service = ReplicateService(db)

    try:
        replicate = replicate_service.get_by_id(uuid.UUID(replicate_id))
    except ValueError:
        return RedirectResponse(
            url=f"/projects/{project.id}/experiments/{experiment.id}/replicates",
            status_code=status.HTTP_302_FOUND,
        )

    if replicate and replicate.experiment_id == experiment.id:
        replicate_service.delete_replicate(replicate)

    return RedirectResponse(
        url=f"/projects/{project.id}/experiments/{experiment.id}/replicates",
        status_code=status.HTTP_302_FOUND,
    )
