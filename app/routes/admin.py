"""Admin routes for user management."""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin
from app.database import get_db
from app.models.user import User
from app.services.user import UserService
from app.services.password import generate_temp_password


router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")


@router.get("/users", response_class=HTMLResponse)
async def list_users(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    show_inactive: bool = False,
):
    """List all users.

    Args:
        request: FastAPI request.
        db: Database session.
        admin: Current admin user.
        show_inactive: Whether to show inactive users.

    Returns:
        User list page.
    """
    user_service = UserService(db)
    users = user_service.list_users(include_inactive=show_inactive)

    return templates.TemplateResponse(
        "admin/users.html",
        {
            "request": request,
            "user": admin,
            "users": users,
            "show_inactive": show_inactive,
        },
    )


@router.get("/users/new", response_class=HTMLResponse)
async def new_user_form(
    request: Request,
    admin: Annotated[User, Depends(require_admin)],
):
    """Show create user form.

    Args:
        request: FastAPI request.
        admin: Current admin user.

    Returns:
        New user form page.
    """
    return templates.TemplateResponse(
        "admin/user_form.html",
        {
            "request": request,
            "user": admin,
            "form_user": None,
            "error": None,
            "temp_password": None,
        },
    )


@router.post("/users/new")
async def create_user(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    email: Annotated[str, Form()],
    name: Annotated[str, Form()],
    is_admin: Annotated[bool, Form()] = False,
):
    """Create a new user.

    Args:
        request: FastAPI request.
        db: Database session.
        admin: Current admin user.
        email: New user's email.
        name: New user's name.
        is_admin: Whether new user is admin.

    Returns:
        Redirect to user list or form with error.
    """
    user_service = UserService(db)

    # Generate temporary password
    temp_password = generate_temp_password()

    try:
        new_user = user_service.create_user(
            email=email,
            name=name,
            password=temp_password,
            is_admin=is_admin,
        )

        # Show success with temporary password
        return templates.TemplateResponse(
            "admin/user_created.html",
            {
                "request": request,
                "user": admin,
                "new_user": new_user,
                "temp_password": temp_password,
            },
        )
    except ValueError as e:
        return templates.TemplateResponse(
            "admin/user_form.html",
            {
                "request": request,
                "user": admin,
                "form_user": None,
                "error": str(e),
                "email": email,
                "name": name,
                "is_admin": is_admin,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@router.get("/users/{user_id}", response_class=HTMLResponse)
async def view_user(
    request: Request,
    user_id: str,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
):
    """View user details.

    Args:
        request: FastAPI request.
        user_id: User UUID.
        db: Database session.
        admin: Current admin user.

    Returns:
        User detail page.
    """
    import uuid

    user_service = UserService(db)

    try:
        target_user = user_service.get_by_id(uuid.UUID(user_id))
    except ValueError:
        return RedirectResponse(
            url="/admin/users",
            status_code=status.HTTP_302_FOUND,
        )

    if not target_user:
        return RedirectResponse(
            url="/admin/users",
            status_code=status.HTTP_302_FOUND,
        )

    return templates.TemplateResponse(
        "admin/user_detail.html",
        {
            "request": request,
            "user": admin,
            "target_user": target_user,
        },
    )


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
):
    """Deactivate a user.

    Args:
        user_id: User UUID.
        db: Database session.
        admin: Current admin user.

    Returns:
        Redirect to user list.
    """
    import uuid

    user_service = UserService(db)

    try:
        target_user = user_service.get_by_id(uuid.UUID(user_id))
    except ValueError:
        return RedirectResponse(
            url="/admin/users",
            status_code=status.HTTP_302_FOUND,
        )

    if target_user and target_user.id != admin.id:
        user_service.deactivate_user(target_user)

    return RedirectResponse(
        url="/admin/users",
        status_code=status.HTTP_302_FOUND,
    )


@router.post("/users/{user_id}/reactivate")
async def reactivate_user(
    user_id: str,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
):
    """Reactivate a user.

    Args:
        user_id: User UUID.
        db: Database session.
        admin: Current admin user.

    Returns:
        Redirect to user list.
    """
    import uuid

    user_service = UserService(db)

    try:
        target_user = user_service.get_by_id(uuid.UUID(user_id))
    except ValueError:
        return RedirectResponse(
            url="/admin/users?show_inactive=true",
            status_code=status.HTTP_302_FOUND,
        )

    if target_user:
        user_service.reactivate_user(target_user)

    return RedirectResponse(
        url="/admin/users",
        status_code=status.HTTP_302_FOUND,
    )


@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    request: Request,
    user_id: str,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
):
    """Reset a user's password.

    Args:
        request: FastAPI request.
        user_id: User UUID.
        db: Database session.
        admin: Current admin user.

    Returns:
        Page showing new temporary password.
    """
    import uuid

    user_service = UserService(db)

    try:
        target_user = user_service.get_by_id(uuid.UUID(user_id))
    except ValueError:
        return RedirectResponse(
            url="/admin/users",
            status_code=status.HTTP_302_FOUND,
        )

    if not target_user:
        return RedirectResponse(
            url="/admin/users",
            status_code=status.HTTP_302_FOUND,
        )

    # Generate and set new password
    temp_password = generate_temp_password()
    user_service.reset_password(target_user, temp_password)

    return templates.TemplateResponse(
        "admin/password_reset.html",
        {
            "request": request,
            "user": admin,
            "target_user": target_user,
            "temp_password": temp_password,
        },
    )
