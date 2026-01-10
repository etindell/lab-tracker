"""Authentication routes."""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Form, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth.dependencies import (
    SESSION_COOKIE_NAME,
    get_current_user_optional,
    get_session_token,
)
from app.auth.session import SessionService
from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.services.user import UserService


router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="templates")
settings = get_settings()


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    user: Annotated[Optional[User], Depends(get_current_user_optional)],
    error: Optional[str] = None,
    next: Optional[str] = None,
):
    """Render login page.

    Args:
        request: FastAPI request.
        user: Current user if authenticated.
        error: Error message to display.
        next: URL to redirect to after login.

    Returns:
        Login page HTML or redirect if already logged in.
    """
    # Redirect if already logged in
    if user:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse(
        "auth/login.html",
        {
            "request": request,
            "error": error,
            "next": next,
        },
    )


@router.post("/login")
async def login(
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    remember_me: Annotated[bool, Form()] = False,
    next: Annotated[Optional[str], Form()] = None,
):
    """Process login form submission.

    Args:
        request: FastAPI request.
        response: FastAPI response.
        db: Database session.
        email: User email.
        password: User password.
        remember_me: Whether to extend session.
        next: URL to redirect to after login.

    Returns:
        Redirect to dashboard or back to login with error.
    """
    user_service = UserService(db)
    user = user_service.authenticate(email, password)

    if not user:
        return templates.TemplateResponse(
            "auth/login.html",
            {
                "request": request,
                "error": "Invalid email or password",
                "next": next,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Create session
    session_service = SessionService(db)
    token = session_service.create_session(user, remember_me=remember_me)

    # Set cookie
    redirect_url = next if next else "/"
    redirect_response = RedirectResponse(
        url=redirect_url,
        status_code=status.HTTP_302_FOUND,
    )

    # Cookie settings
    max_age = (
        settings.session_expire_remember_seconds
        if remember_me
        else settings.session_expire_seconds
    )

    redirect_response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=max_age,
        httponly=True,
        samesite="lax",
        secure=settings.is_production,
    )

    return redirect_response


@router.get("/logout")
@router.post("/logout")
async def logout(
    db: Annotated[Session, Depends(get_db)],
    token: Annotated[Optional[str], Depends(get_session_token)],
):
    """Log out current user.

    Args:
        db: Database session.
        token: Current session token.

    Returns:
        Redirect to login page.
    """
    if token:
        session_service = SessionService(db)
        session_service.delete_session(token)

    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key=SESSION_COOKIE_NAME)
    return response
