"""FastAPI application entry point."""

import logging
import os
import subprocess
import sys
from contextlib import asynccontextmanager
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, Request, status
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user_optional
from app.config import get_settings
from app.database import get_db
from app.flash import get_flash_messages
from app.models.user import User
from app.routes.auth import router as auth_router
from app.routes.admin import router as admin_router
from app.routes.projects import router as projects_router
from app.routes.experiments import router as experiments_router
from app.routes.replicates import router as replicates_router
from app.routes.todos import router as todos_router
from app.routes.notes import router as notes_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

settings = get_settings()


def run_migrations():
    """Run database migrations on startup."""
    from sqlalchemy import inspect
    from app.database import engine, Base
    from app import models  # Import all models to register them

    try:
        logger.info("Running database migrations...")
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        logger.info(f"Alembic result: {result.returncode}")
        if result.stdout:
            logger.info(f"Alembic stdout: {result.stdout}")
        if result.stderr:
            logger.info(f"Alembic stderr: {result.stderr}")

        # Check if tables actually exist after alembic
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"Tables after alembic: {tables}")

        if "users" not in tables:
            logger.info("Users table missing, running create_all...")
            Base.metadata.create_all(bind=engine)
            tables_after = inspect(engine).get_table_names()
            logger.info(f"Tables after create_all: {tables_after}")

    except Exception as e:
        logger.warning(f"Migration error: {e}, trying create_all fallback")
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Tables created via create_all fallback")
        except Exception as e2:
            logger.error(f"create_all also failed: {e2}")


def create_admin_user():
    """Create default admin user if not exists, or reset password if RESET_ADMIN env var is set."""
    from app.database import SessionLocal
    from app.services.user import UserService
    from app.services.password import generate_temp_password

    db = SessionLocal()
    try:
        service = UserService(db)
        admin = service.get_by_email("admin@labtracker.local")
        reset_admin = os.environ.get("RESET_ADMIN", "").lower() == "true"

        if not admin:
            password = generate_temp_password()
            service.create_user(
                email="admin@labtracker.local",
                name="Admin",
                password=password,
                is_admin=True,
            )
            logger.info(f"Created admin user: admin@labtracker.local")
            logger.info(f"PASSWORD: {password}")
            logger.info("Please change this password after first login!")
        elif reset_admin:
            password = generate_temp_password()
            service.reset_password(admin, password)
            logger.info(f"Reset admin password for: admin@labtracker.local")
            logger.info(f"PASSWORD: {password}")
            logger.info("Please change this password after first login!")
        else:
            logger.info("Admin user already exists (set RESET_ADMIN=true to reset password)")
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info(f"Starting {settings.app_name} in {settings.environment} mode")

    # Run migrations and create admin on startup
    if settings.is_production:
        run_migrations()
        create_admin_user()

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
app.include_router(projects_router)
app.include_router(experiments_router)
app.include_router(replicates_router)
app.include_router(todos_router)
app.include_router(notes_router)


# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: StarletteHTTPException):
    """Handle 404 errors with custom page."""
    return templates.TemplateResponse(
        "errors/404.html",
        {"request": request},
        status_code=404,
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc: Exception):
    """Handle 500 errors with custom page."""
    logger.error(f"Server error: {exc}")
    return templates.TemplateResponse(
        "errors/500.html",
        {"request": request},
        status_code=500,
    )


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
    db: Annotated[Session, Depends(get_db)],
):
    """Root endpoint - redirects to login or dashboard.

    Args:
        request: FastAPI request.
        user: Current user if authenticated.
        db: Database session.

    Returns:
        Redirect to appropriate page.
    """
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    # Import services here to avoid circular imports
    from app.services.project import ProjectService
    from app.services.todo import TodoService
    from app.services.activity import ActivityService

    project_service = ProjectService(db)
    todo_service = TodoService(db)
    activity_service = ActivityService(db)

    # Get stats
    projects = project_service.list_projects()
    total_experiments = sum(len(p.experiments) for p in projects)
    total_replicates = sum(
        sum(len(e.replicates) for e in p.experiments)
        for p in projects
    )

    # Get user's assigned todos
    my_todos = todo_service.list_todos(user=user, include_done=False)

    # Get recent activities
    recent_activities = activity_service.get_recent_activities(limit=10)

    # Get recent projects (most recently updated)
    recent_projects = projects[:5]  # Already sorted by update time

    stats = {
        "project_count": len(projects),
        "experiment_count": total_experiments,
        "replicate_count": total_replicates,
        "todo_count": len(my_todos),
    }

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "stats": stats,
            "my_todos": my_todos[:5],  # Show only 5 most recent
            "recent_activities": recent_activities,
            "recent_projects": recent_projects,
            "flash_messages": get_flash_messages(request),
        },
    )
