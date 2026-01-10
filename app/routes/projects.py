"""Project routes."""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.flash import add_flash, get_flash_messages
from app.models.project import ProjectStatus
from app.models.user import User
from app.services.activity import ActivityService
from app.services.project import ProjectService


router = APIRouter(prefix="/projects", tags=["projects"])
templates = Jinja2Templates(directory="templates")


@router.get("", response_class=HTMLResponse)
async def list_projects(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
    show_archived: bool = False,
):
    """List all projects.

    Args:
        request: FastAPI request.
        db: Database session.
        user: Current user.
        status_filter: Filter by status.
        search: Search by name.
        show_archived: Show archived projects.

    Returns:
        Project list page.
    """
    project_service = ProjectService(db)

    # Parse status filter
    parsed_status = None
    if status_filter and status_filter != "all":
        try:
            parsed_status = ProjectStatus(status_filter)
        except ValueError:
            pass

    projects = project_service.list_projects(
        status_filter=parsed_status,
        include_archived=show_archived,
        search=search,
    )

    return templates.TemplateResponse(
        "projects/list.html",
        {
            "request": request,
            "user": user,
            "projects": projects,
            "status_filter": status_filter or "all",
            "search": search or "",
            "show_archived": show_archived,
            "statuses": ProjectStatus,
            "flash_messages": get_flash_messages(request),
        },
    )


@router.get("/new", response_class=HTMLResponse)
async def new_project_form(
    request: Request,
    user: Annotated[User, Depends(get_current_user)],
):
    """Show create project form.

    Args:
        request: FastAPI request.
        user: Current user.

    Returns:
        New project form page.
    """
    return templates.TemplateResponse(
        "projects/form.html",
        {
            "request": request,
            "user": user,
            "project": None,
            "error": None,
            "statuses": ProjectStatus,
        },
    )


@router.post("/new")
async def create_project(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    name: Annotated[str, Form()],
    description: Annotated[str, Form()] = "",
    project_status: Annotated[str, Form()] = "active",
):
    """Create a new project.

    Args:
        request: FastAPI request.
        db: Database session.
        user: Current user.
        name: Project name.
        description: Project description.
        project_status: Initial status.

    Returns:
        Redirect to project or form with error.
    """
    project_service = ProjectService(db)

    try:
        parsed_status = ProjectStatus(project_status)
    except ValueError:
        parsed_status = ProjectStatus.ACTIVE

    try:
        project = project_service.create_project(
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
            entity_type="project",
            entity_id=project.id,
            metadata={"name": project.name},
        )

        add_flash(request, f"Project '{project.name}' created successfully", "success")
        return RedirectResponse(
            url=f"/projects/{project.id}",
            status_code=status.HTTP_302_FOUND,
        )
    except ValueError as e:
        return templates.TemplateResponse(
            "projects/form.html",
            {
                "request": request,
                "user": user,
                "project": None,
                "error": str(e),
                "name": name,
                "description": description,
                "project_status": project_status,
                "statuses": ProjectStatus,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@router.get("/{project_id}", response_class=HTMLResponse)
async def view_project(
    request: Request,
    project_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """View project details.

    Args:
        request: FastAPI request.
        project_id: Project UUID.
        db: Database session.
        user: Current user.

    Returns:
        Project detail page.
    """
    import uuid

    project_service = ProjectService(db)

    try:
        project = project_service.get_by_id(uuid.UUID(project_id))
    except ValueError:
        return RedirectResponse(
            url="/projects",
            status_code=status.HTTP_302_FOUND,
        )

    if not project:
        return RedirectResponse(
            url="/projects",
            status_code=status.HTTP_302_FOUND,
        )

    stats = project_service.get_project_stats(project)

    return templates.TemplateResponse(
        "projects/detail.html",
        {
            "request": request,
            "user": user,
            "project": project,
            "stats": stats,
            "flash_messages": get_flash_messages(request),
        },
    )


@router.get("/{project_id}/edit", response_class=HTMLResponse)
async def edit_project_form(
    request: Request,
    project_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Show edit project form.

    Args:
        request: FastAPI request.
        project_id: Project UUID.
        db: Database session.
        user: Current user.

    Returns:
        Edit project form page.
    """
    import uuid

    project_service = ProjectService(db)

    try:
        project = project_service.get_by_id(uuid.UUID(project_id))
    except ValueError:
        return RedirectResponse(
            url="/projects",
            status_code=status.HTTP_302_FOUND,
        )

    if not project:
        return RedirectResponse(
            url="/projects",
            status_code=status.HTTP_302_FOUND,
        )

    return templates.TemplateResponse(
        "projects/form.html",
        {
            "request": request,
            "user": user,
            "project": project,
            "error": None,
            "statuses": ProjectStatus,
        },
    )


@router.post("/{project_id}/edit")
async def update_project(
    request: Request,
    project_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    name: Annotated[str, Form()],
    description: Annotated[str, Form()] = "",
    project_status: Annotated[str, Form()] = "active",
):
    """Update a project.

    Args:
        request: FastAPI request.
        project_id: Project UUID.
        db: Database session.
        user: Current user.
        name: Project name.
        description: Project description.
        project_status: Project status.

    Returns:
        Redirect to project or form with error.
    """
    import uuid

    project_service = ProjectService(db)

    try:
        project = project_service.get_by_id(uuid.UUID(project_id))
    except ValueError:
        return RedirectResponse(
            url="/projects",
            status_code=status.HTTP_302_FOUND,
        )

    if not project:
        return RedirectResponse(
            url="/projects",
            status_code=status.HTTP_302_FOUND,
        )

    try:
        parsed_status = ProjectStatus(project_status)
    except ValueError:
        parsed_status = project.status

    try:
        project_service.update_project(
            project=project,
            name=name,
            description=description,
            status=parsed_status,
        )

        # Log activity
        activity_service = ActivityService(db)
        activity_service.log_activity(
            user=user,
            action="update",
            entity_type="project",
            entity_id=project.id,
            metadata={"name": project.name},
        )

        add_flash(request, f"Project '{project.name}' updated successfully", "success")
        return RedirectResponse(
            url=f"/projects/{project.id}",
            status_code=status.HTTP_302_FOUND,
        )
    except ValueError as e:
        return templates.TemplateResponse(
            "projects/form.html",
            {
                "request": request,
                "user": user,
                "project": project,
                "error": str(e),
                "name": name,
                "description": description,
                "project_status": project_status,
                "statuses": ProjectStatus,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@router.post("/{project_id}/archive")
async def archive_project(
    request: Request,
    project_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Archive a project.

    Args:
        request: FastAPI request.
        project_id: Project UUID.
        db: Database session.
        user: Current user.

    Returns:
        Redirect to projects list.
    """
    import uuid

    project_service = ProjectService(db)

    try:
        project = project_service.get_by_id(uuid.UUID(project_id))
    except ValueError:
        return RedirectResponse(
            url="/projects",
            status_code=status.HTTP_302_FOUND,
        )

    if project:
        project_name = project.name
        project_service.archive_project(project)

        # Log activity
        activity_service = ActivityService(db)
        activity_service.log_activity(
            user=user,
            action="archive",
            entity_type="project",
            entity_id=project.id,
            metadata={"name": project_name},
        )

        add_flash(request, f"Project '{project_name}' archived", "success")

    return RedirectResponse(
        url="/projects",
        status_code=status.HTTP_302_FOUND,
    )
