"""Note routes."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.services.experiment import ExperimentService
from app.services.note import NoteService
from app.services.project import ProjectService
from app.services.replicate import ReplicateService


router = APIRouter(tags=["notes"])
templates = Jinja2Templates(directory="templates")


# Notes on experiments
@router.post(
    "/projects/{project_id}/experiments/{experiment_id}/notes/new"
)
async def create_experiment_note(
    project_id: str,
    experiment_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    content: Annotated[str, Form()] = "",
):
    """Create a note on an experiment.

    Args:
        project_id: Project UUID.
        experiment_id: Experiment UUID.
        db: Database session.
        user: Current user.
        content: Note content.

    Returns:
        Redirect to experiment detail page.
    """
    project_service = ProjectService(db)
    experiment_service = ExperimentService(db)
    note_service = NoteService(db)

    try:
        project = project_service.get_by_id(uuid.UUID(project_id))
        experiment = experiment_service.get_by_id(uuid.UUID(experiment_id))
    except ValueError:
        return RedirectResponse(
            url="/projects",
            status_code=status.HTTP_302_FOUND,
        )

    if not project or not experiment or experiment.project_id != project.id:
        return RedirectResponse(
            url="/projects",
            status_code=status.HTTP_302_FOUND,
        )

    if content.strip():
        note_service.create_note(
            content=content.strip(),
            author=user,
            experiment=experiment,
        )

    return RedirectResponse(
        url=f"/projects/{project.id}/experiments/{experiment.id}",
        status_code=status.HTTP_302_FOUND,
    )


@router.get(
    "/projects/{project_id}/experiments/{experiment_id}/notes/{note_id}/edit",
    response_class=HTMLResponse,
)
async def edit_experiment_note_form(
    request: Request,
    project_id: str,
    experiment_id: str,
    note_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Show edit note form.

    Args:
        request: FastAPI request.
        project_id: Project UUID.
        experiment_id: Experiment UUID.
        note_id: Note UUID.
        db: Database session.
        user: Current user.

    Returns:
        Edit note form page.
    """
    project_service = ProjectService(db)
    experiment_service = ExperimentService(db)
    note_service = NoteService(db)

    try:
        project = project_service.get_by_id(uuid.UUID(project_id))
        experiment = experiment_service.get_by_id(uuid.UUID(experiment_id))
        note = note_service.get_by_id(uuid.UUID(note_id))
    except ValueError:
        return RedirectResponse(
            url="/projects",
            status_code=status.HTTP_302_FOUND,
        )

    if (
        not project
        or not experiment
        or not note
        or experiment.project_id != project.id
        or note.experiment_id != experiment.id
    ):
        return RedirectResponse(
            url="/projects",
            status_code=status.HTTP_302_FOUND,
        )

    return templates.TemplateResponse(
        "notes/form.html",
        {
            "request": request,
            "user": user,
            "project": project,
            "experiment": experiment,
            "replicate": None,
            "note": note,
        },
    )


@router.post(
    "/projects/{project_id}/experiments/{experiment_id}/notes/{note_id}/edit"
)
async def update_experiment_note(
    project_id: str,
    experiment_id: str,
    note_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    content: Annotated[str, Form()],
):
    """Update a note on an experiment.

    Args:
        project_id: Project UUID.
        experiment_id: Experiment UUID.
        note_id: Note UUID.
        db: Database session.
        user: Current user.
        content: Updated content.

    Returns:
        Redirect to experiment detail page.
    """
    project_service = ProjectService(db)
    experiment_service = ExperimentService(db)
    note_service = NoteService(db)

    try:
        project = project_service.get_by_id(uuid.UUID(project_id))
        experiment = experiment_service.get_by_id(uuid.UUID(experiment_id))
        note = note_service.get_by_id(uuid.UUID(note_id))
    except ValueError:
        return RedirectResponse(
            url="/projects",
            status_code=status.HTTP_302_FOUND,
        )

    if (
        not project
        or not experiment
        or not note
        or experiment.project_id != project.id
        or note.experiment_id != experiment.id
    ):
        return RedirectResponse(
            url="/projects",
            status_code=status.HTTP_302_FOUND,
        )

    note_service.update_note(note, content=content.strip())

    return RedirectResponse(
        url=f"/projects/{project.id}/experiments/{experiment.id}",
        status_code=status.HTTP_302_FOUND,
    )


@router.post(
    "/projects/{project_id}/experiments/{experiment_id}/notes/{note_id}/delete"
)
async def delete_experiment_note(
    project_id: str,
    experiment_id: str,
    note_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Delete a note from an experiment.

    Args:
        project_id: Project UUID.
        experiment_id: Experiment UUID.
        note_id: Note UUID.
        db: Database session.
        user: Current user.

    Returns:
        Redirect to experiment detail page.
    """
    project_service = ProjectService(db)
    experiment_service = ExperimentService(db)
    note_service = NoteService(db)

    try:
        project = project_service.get_by_id(uuid.UUID(project_id))
        experiment = experiment_service.get_by_id(uuid.UUID(experiment_id))
        note = note_service.get_by_id(uuid.UUID(note_id))
    except ValueError:
        return RedirectResponse(
            url="/projects",
            status_code=status.HTTP_302_FOUND,
        )

    if (
        not project
        or not experiment
        or not note
        or experiment.project_id != project.id
        or note.experiment_id != experiment.id
    ):
        return RedirectResponse(
            url="/projects",
            status_code=status.HTTP_302_FOUND,
        )

    note_service.delete_note(note)

    return RedirectResponse(
        url=f"/projects/{project.id}/experiments/{experiment.id}",
        status_code=status.HTTP_302_FOUND,
    )


# Notes on replicates
@router.post(
    "/projects/{project_id}/experiments/{experiment_id}/replicates/{replicate_id}/notes/new"
)
async def create_replicate_note(
    project_id: str,
    experiment_id: str,
    replicate_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    content: Annotated[str, Form()] = "",
):
    """Create a note on a replicate.

    Args:
        project_id: Project UUID.
        experiment_id: Experiment UUID.
        replicate_id: Replicate UUID.
        db: Database session.
        user: Current user.
        content: Note content.

    Returns:
        Redirect to replicate detail page.
    """
    project_service = ProjectService(db)
    experiment_service = ExperimentService(db)
    replicate_service = ReplicateService(db)
    note_service = NoteService(db)

    try:
        project = project_service.get_by_id(uuid.UUID(project_id))
        experiment = experiment_service.get_by_id(uuid.UUID(experiment_id))
        replicate = replicate_service.get_by_id(uuid.UUID(replicate_id))
    except ValueError:
        return RedirectResponse(
            url="/projects",
            status_code=status.HTTP_302_FOUND,
        )

    if (
        not project
        or not experiment
        or not replicate
        or experiment.project_id != project.id
        or replicate.experiment_id != experiment.id
    ):
        return RedirectResponse(
            url="/projects",
            status_code=status.HTTP_302_FOUND,
        )

    if content.strip():
        note_service.create_note(
            content=content.strip(),
            author=user,
            replicate=replicate,
        )

    return RedirectResponse(
        url=f"/projects/{project.id}/experiments/{experiment.id}/replicates/{replicate.id}",
        status_code=status.HTTP_302_FOUND,
    )


@router.get(
    "/projects/{project_id}/experiments/{experiment_id}/replicates/{replicate_id}/notes/{note_id}/edit",
    response_class=HTMLResponse,
)
async def edit_replicate_note_form(
    request: Request,
    project_id: str,
    experiment_id: str,
    replicate_id: str,
    note_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Show edit note form for replicate note.

    Args:
        request: FastAPI request.
        project_id: Project UUID.
        experiment_id: Experiment UUID.
        replicate_id: Replicate UUID.
        note_id: Note UUID.
        db: Database session.
        user: Current user.

    Returns:
        Edit note form page.
    """
    project_service = ProjectService(db)
    experiment_service = ExperimentService(db)
    replicate_service = ReplicateService(db)
    note_service = NoteService(db)

    try:
        project = project_service.get_by_id(uuid.UUID(project_id))
        experiment = experiment_service.get_by_id(uuid.UUID(experiment_id))
        replicate = replicate_service.get_by_id(uuid.UUID(replicate_id))
        note = note_service.get_by_id(uuid.UUID(note_id))
    except ValueError:
        return RedirectResponse(
            url="/projects",
            status_code=status.HTTP_302_FOUND,
        )

    if (
        not project
        or not experiment
        or not replicate
        or not note
        or experiment.project_id != project.id
        or replicate.experiment_id != experiment.id
        or note.replicate_id != replicate.id
    ):
        return RedirectResponse(
            url="/projects",
            status_code=status.HTTP_302_FOUND,
        )

    return templates.TemplateResponse(
        "notes/form.html",
        {
            "request": request,
            "user": user,
            "project": project,
            "experiment": experiment,
            "replicate": replicate,
            "note": note,
        },
    )


@router.post(
    "/projects/{project_id}/experiments/{experiment_id}/replicates/{replicate_id}/notes/{note_id}/edit"
)
async def update_replicate_note(
    project_id: str,
    experiment_id: str,
    replicate_id: str,
    note_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    content: Annotated[str, Form()],
):
    """Update a note on a replicate.

    Args:
        project_id: Project UUID.
        experiment_id: Experiment UUID.
        replicate_id: Replicate UUID.
        note_id: Note UUID.
        db: Database session.
        user: Current user.
        content: Updated content.

    Returns:
        Redirect to replicate detail page.
    """
    project_service = ProjectService(db)
    experiment_service = ExperimentService(db)
    replicate_service = ReplicateService(db)
    note_service = NoteService(db)

    try:
        project = project_service.get_by_id(uuid.UUID(project_id))
        experiment = experiment_service.get_by_id(uuid.UUID(experiment_id))
        replicate = replicate_service.get_by_id(uuid.UUID(replicate_id))
        note = note_service.get_by_id(uuid.UUID(note_id))
    except ValueError:
        return RedirectResponse(
            url="/projects",
            status_code=status.HTTP_302_FOUND,
        )

    if (
        not project
        or not experiment
        or not replicate
        or not note
        or experiment.project_id != project.id
        or replicate.experiment_id != experiment.id
        or note.replicate_id != replicate.id
    ):
        return RedirectResponse(
            url="/projects",
            status_code=status.HTTP_302_FOUND,
        )

    note_service.update_note(note, content=content.strip())

    return RedirectResponse(
        url=f"/projects/{project.id}/experiments/{experiment.id}/replicates/{replicate.id}",
        status_code=status.HTTP_302_FOUND,
    )


@router.post(
    "/projects/{project_id}/experiments/{experiment_id}/replicates/{replicate_id}/notes/{note_id}/delete"
)
async def delete_replicate_note(
    project_id: str,
    experiment_id: str,
    replicate_id: str,
    note_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Delete a note from a replicate.

    Args:
        project_id: Project UUID.
        experiment_id: Experiment UUID.
        replicate_id: Replicate UUID.
        note_id: Note UUID.
        db: Database session.
        user: Current user.

    Returns:
        Redirect to replicate detail page.
    """
    project_service = ProjectService(db)
    experiment_service = ExperimentService(db)
    replicate_service = ReplicateService(db)
    note_service = NoteService(db)

    try:
        project = project_service.get_by_id(uuid.UUID(project_id))
        experiment = experiment_service.get_by_id(uuid.UUID(experiment_id))
        replicate = replicate_service.get_by_id(uuid.UUID(replicate_id))
        note = note_service.get_by_id(uuid.UUID(note_id))
    except ValueError:
        return RedirectResponse(
            url="/projects",
            status_code=status.HTTP_302_FOUND,
        )

    if (
        not project
        or not experiment
        or not replicate
        or not note
        or experiment.project_id != project.id
        or replicate.experiment_id != experiment.id
        or note.replicate_id != replicate.id
    ):
        return RedirectResponse(
            url="/projects",
            status_code=status.HTTP_302_FOUND,
        )

    note_service.delete_note(note)

    return RedirectResponse(
        url=f"/projects/{project.id}/experiments/{experiment.id}/replicates/{replicate.id}",
        status_code=status.HTTP_302_FOUND,
    )
