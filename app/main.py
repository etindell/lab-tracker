"""FastAPI application entry point."""

import logging
import sys
from contextlib import asynccontextmanager
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.auth.dependencies import get_current_user_optional
from app.config import get_settings
from app.models.user import User
from app.routes.auth import router as auth_router
from app.routes.admin import router as admin_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info(f"Starting {settings.app_name} in {settings.environment} mode")
    yield
    logger.info(f"Shutting down {settings.app_name}")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Web-based project tracking for research labs",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(auth_router)
app.include_router(admin_router)


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint for monitoring and deployment."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "environment": settings.environment,
    }


@app.get("/", response_class=HTMLResponse)
async def root(
    request: Request,
    user: Annotated[Optional[User], Depends(get_current_user_optional)],
):
    """Root endpoint - redirects to login or dashboard.

    Args:
        request: FastAPI request.
        user: Current user if authenticated.

    Returns:
        Redirect to appropriate page.
    """
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    # For now, show a simple dashboard placeholder
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
        },
    )
