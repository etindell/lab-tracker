"""Todo routes."""

import uuid
from datetime import date, datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.todo import TodoPriority, TodoStatus
from app.models.user import User
from app.services.experiment import ExperimentService
from app.services.project import ProjectService
from app.services.todo import TodoService
from app.services.user import UserService


router = APIRouter(prefix="/todos", tags=["todos"])
templates = Jinja2Templates(directory="templates")


@router.get("", response_class=HTMLResponse)
async def list_todos(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    status_filter: Optional[str] = None,
    priority_filter: Optional[str] = None,
    project_id: Optional[str] = None,
    search: Optional[str] = None,
    show_done: bool = False,
    my_todos: bool = True,
):
    """List all todos.

    Args:
        request: FastAPI request.
        db: Database session.
        user: Current user.
        status_filter: Filter by status.
        priority_filter: Filter by priority.
        project_id: Filter by project.
        search: Search by title.
        show_done: Show done todos.
        my_todos: Show only user's todos.

    Returns:
        Todo list page.
    """
    todo_service = TodoService(db)
    project_service = ProjectService(db)

    parsed_status = None
    if status_filter and status_filter != "all":
        try:
            parsed_status = TodoStatus(status_filter)
        except ValueError:
            pass

    parsed_priority = None
    if priority_filter and priority_filter != "all":
        try:
            parsed_priority = TodoPriority(priority_filter)
        except ValueError:
            pass

    project = None
    if project_id:
        try:
            project = project_service.get_by_id(uuid.UUID(project_id))
        except ValueError:
            pass

    todos = todo_service.list_todos(
        user=user if my_todos else None,
        status_filter=parsed_status,
        priority_filter=parsed_priority,
        project=project,
        search=search,
        include_done=show_done or parsed_status == TodoStatus.DONE,
    )

    projects = project_service.list_projects()

    return templates.TemplateResponse(
        "todos/list.html",
        {
            "request": request,
            "user": user,
            "todos": todos,
            "status_filter": status_filter or "all",
            "priority_filter": priority_filter or "all",
            "project_id": project_id or "",
            "search": search or "",
            "show_done": show_done,
            "my_todos": my_todos,
            "statuses": TodoStatus,
            "priorities": TodoPriority,
            "projects": projects,
        },
    )


@router.get("/kanban", response_class=HTMLResponse)
async def kanban_board(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    project_id: Optional[str] = None,
    my_todos: bool = True,
):
    """Show todo kanban board.

    Args:
        request: FastAPI request.
        db: Database session.
        user: Current user.
        project_id: Filter by project.
        my_todos: Show only user's todos.

    Returns:
        Kanban board page.
    """
    todo_service = TodoService(db)
    project_service = ProjectService(db)

    project = None
    if project_id:
        try:
            project = project_service.get_by_id(uuid.UUID(project_id))
        except ValueError:
            pass

    # Get todos grouped by status
    todos_by_status = {}
    for todo_status in TodoStatus:
        todos_by_status[todo_status.value] = todo_service.list_todos(
            user=user if my_todos else None,
            status_filter=todo_status,
            project=project,
        )

    projects = project_service.list_projects()

    return templates.TemplateResponse(
        "todos/kanban.html",
        {
            "request": request,
            "user": user,
            "todos_by_status": todos_by_status,
            "project_id": project_id or "",
            "my_todos": my_todos,
            "statuses": TodoStatus,
            "projects": projects,
        },
    )


@router.get("/new", response_class=HTMLResponse)
async def new_todo_form(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    project_id: Optional[str] = None,
    experiment_id: Optional[str] = None,
):
    """Show create todo form.

    Args:
        request: FastAPI request.
        db: Database session.
        user: Current user.
        project_id: Pre-select project.
        experiment_id: Pre-select experiment.

    Returns:
        New todo form page.
    """
    project_service = ProjectService(db)
    user_service = UserService(db)

    projects = project_service.list_projects()
    users = user_service.list_users()

    return templates.TemplateResponse(
        "todos/form.html",
        {
            "request": request,
            "user": user,
            "todo": None,
            "error": None,
            "statuses": TodoStatus,
            "priorities": TodoPriority,
            "projects": projects,
            "users": users,
            "selected_project_id": project_id or "",
            "selected_experiment_id": experiment_id or "",
        },
    )


@router.post("/new")
async def create_todo(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    title: Annotated[str, Form()],
    description: Annotated[str, Form()] = "",
    priority: Annotated[str, Form()] = "medium",
    due_date: Annotated[str, Form()] = "",
    assigned_to_id: Annotated[str, Form()] = "",
    project_id: Annotated[str, Form()] = "",
    experiment_id: Annotated[str, Form()] = "",
):
    """Create a new todo.

    Args:
        request: FastAPI request.
        db: Database session.
        user: Current user.
        title: Todo title.
        description: Todo description.
        priority: Todo priority.
        due_date: Due date string.
        assigned_to_id: Assignee user ID.
        project_id: Project ID to link.
        experiment_id: Experiment ID to link.

    Returns:
        Redirect to todo or form with error.
    """
    todo_service = TodoService(db)
    project_service = ProjectService(db)
    experiment_service = ExperimentService(db)
    user_service = UserService(db)

    try:
        parsed_priority = TodoPriority(priority)
    except ValueError:
        parsed_priority = TodoPriority.MEDIUM

    parsed_due_date = None
    if due_date:
        try:
            parsed_due_date = datetime.strptime(due_date, "%Y-%m-%d").date()
        except ValueError:
            pass

    assignee = None
    if assigned_to_id:
        try:
            assignee = user_service.get_by_id(uuid.UUID(assigned_to_id))
        except ValueError:
            pass

    project = None
    if project_id:
        try:
            project = project_service.get_by_id(uuid.UUID(project_id))
        except ValueError:
            pass

    experiment = None
    if experiment_id:
        try:
            experiment = experiment_service.get_by_id(uuid.UUID(experiment_id))
        except ValueError:
            pass

    todo = todo_service.create_todo(
        title=title,
        created_by=user,
        description=description,
        priority=parsed_priority,
        due_date=parsed_due_date,
        assigned_to=assignee,
        project=project,
        experiment=experiment,
    )

    return RedirectResponse(
        url=f"/todos/{todo.id}",
        status_code=status.HTTP_302_FOUND,
    )


@router.get("/{todo_id}", response_class=HTMLResponse)
async def view_todo(
    request: Request,
    todo_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """View todo details.

    Args:
        request: FastAPI request.
        todo_id: Todo UUID.
        db: Database session.
        user: Current user.

    Returns:
        Todo detail page.
    """
    todo_service = TodoService(db)

    try:
        todo = todo_service.get_by_id(uuid.UUID(todo_id))
    except ValueError:
        return RedirectResponse(
            url="/todos",
            status_code=status.HTTP_302_FOUND,
        )

    if not todo:
        return RedirectResponse(
            url="/todos",
            status_code=status.HTTP_302_FOUND,
        )

    return templates.TemplateResponse(
        "todos/detail.html",
        {
            "request": request,
            "user": user,
            "todo": todo,
            "statuses": TodoStatus,
        },
    )


@router.get("/{todo_id}/edit", response_class=HTMLResponse)
async def edit_todo_form(
    request: Request,
    todo_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Show edit todo form.

    Args:
        request: FastAPI request.
        todo_id: Todo UUID.
        db: Database session.
        user: Current user.

    Returns:
        Edit todo form page.
    """
    todo_service = TodoService(db)
    project_service = ProjectService(db)
    user_service = UserService(db)

    try:
        todo = todo_service.get_by_id(uuid.UUID(todo_id))
    except ValueError:
        return RedirectResponse(
            url="/todos",
            status_code=status.HTTP_302_FOUND,
        )

    if not todo:
        return RedirectResponse(
            url="/todos",
            status_code=status.HTTP_302_FOUND,
        )

    projects = project_service.list_projects()
    users = user_service.list_users()

    return templates.TemplateResponse(
        "todos/form.html",
        {
            "request": request,
            "user": user,
            "todo": todo,
            "error": None,
            "statuses": TodoStatus,
            "priorities": TodoPriority,
            "projects": projects,
            "users": users,
            "selected_project_id": str(todo.project_id) if todo.project_id else "",
            "selected_experiment_id": (
                str(todo.experiment_id) if todo.experiment_id else ""
            ),
        },
    )


@router.post("/{todo_id}/edit")
async def update_todo(
    request: Request,
    todo_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    title: Annotated[str, Form()],
    description: Annotated[str, Form()] = "",
    priority: Annotated[str, Form()] = "medium",
    status_value: Annotated[str, Form(alias="status")] = "open",
    due_date: Annotated[str, Form()] = "",
    assigned_to_id: Annotated[str, Form()] = "",
    project_id: Annotated[str, Form()] = "",
):
    """Update a todo.

    Args:
        request: FastAPI request.
        todo_id: Todo UUID.
        db: Database session.
        user: Current user.
        title: Todo title.
        description: Todo description.
        priority: Todo priority.
        status_value: Todo status.
        due_date: Due date string.
        assigned_to_id: Assignee user ID.
        project_id: Project ID to link.

    Returns:
        Redirect to todo or form with error.
    """
    todo_service = TodoService(db)
    project_service = ProjectService(db)
    user_service = UserService(db)

    try:
        todo = todo_service.get_by_id(uuid.UUID(todo_id))
    except ValueError:
        return RedirectResponse(
            url="/todos",
            status_code=status.HTTP_302_FOUND,
        )

    if not todo:
        return RedirectResponse(
            url="/todos",
            status_code=status.HTTP_302_FOUND,
        )

    try:
        parsed_priority = TodoPriority(priority)
    except ValueError:
        parsed_priority = todo.priority

    try:
        parsed_status = TodoStatus(status_value)
    except ValueError:
        parsed_status = todo.status

    parsed_due_date = None
    clear_due_date = False
    if due_date:
        try:
            parsed_due_date = datetime.strptime(due_date, "%Y-%m-%d").date()
        except ValueError:
            pass
    else:
        clear_due_date = True

    assignee = None
    clear_assignee = False
    if assigned_to_id:
        try:
            assignee = user_service.get_by_id(uuid.UUID(assigned_to_id))
        except ValueError:
            pass
    else:
        clear_assignee = True

    project = None
    clear_project = False
    if project_id:
        try:
            project = project_service.get_by_id(uuid.UUID(project_id))
        except ValueError:
            pass
    else:
        clear_project = True

    todo_service.update_todo(
        todo=todo,
        title=title,
        description=description,
        priority=parsed_priority,
        status=parsed_status,
        due_date=parsed_due_date,
        assigned_to=assignee,
        project=project,
        clear_due_date=clear_due_date,
        clear_assignee=clear_assignee,
        clear_project=clear_project,
    )

    return RedirectResponse(
        url=f"/todos/{todo.id}",
        status_code=status.HTTP_302_FOUND,
    )


@router.post("/{todo_id}/status")
async def change_todo_status(
    request: Request,
    todo_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    status_value: Annotated[str, Form(alias="status")],
):
    """Change todo status (inline update for HTMX).

    Args:
        request: FastAPI request.
        todo_id: Todo UUID.
        db: Database session.
        user: Current user.
        status_value: New status value.

    Returns:
        Status badge HTML fragment.
    """
    todo_service = TodoService(db)

    try:
        todo = todo_service.get_by_id(uuid.UUID(todo_id))
    except ValueError:
        return HTMLResponse(content="Invalid todo", status_code=400)

    if not todo:
        return HTMLResponse(content="Todo not found", status_code=404)

    try:
        new_status = TodoStatus(status_value)
    except ValueError:
        return HTMLResponse(content="Invalid status", status_code=400)

    todo_service.change_status(todo, new_status)

    return templates.TemplateResponse(
        "todos/_status_badge.html",
        {
            "request": request,
            "todo": todo,
            "statuses": TodoStatus,
        },
    )


@router.post("/{todo_id}/delete")
async def delete_todo(
    todo_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Delete a todo.

    Args:
        todo_id: Todo UUID.
        db: Database session.
        user: Current user.

    Returns:
        Redirect to todos list.
    """
    todo_service = TodoService(db)

    try:
        todo = todo_service.get_by_id(uuid.UUID(todo_id))
    except ValueError:
        return RedirectResponse(
            url="/todos",
            status_code=status.HTTP_302_FOUND,
        )

    if todo:
        todo_service.delete_todo(todo)

    return RedirectResponse(
        url="/todos",
        status_code=status.HTTP_302_FOUND,
    )
