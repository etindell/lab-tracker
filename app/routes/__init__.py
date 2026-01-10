"""API routes."""

from app.routes.auth import router as auth_router
from app.routes.admin import router as admin_router
from app.routes.projects import router as projects_router
from app.routes.experiments import router as experiments_router
from app.routes.replicates import router as replicates_router

__all__ = [
    "auth_router",
    "admin_router",
    "projects_router",
    "experiments_router",
    "replicates_router",
]
