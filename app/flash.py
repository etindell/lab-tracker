"""Flash message support for displaying one-time notifications."""

from typing import Any
from fastapi import Request
from fastapi.templating import Jinja2Templates


def add_flash(request: Request, message: str, category: str = "info") -> None:
    """Add a flash message to the session.

    Args:
        request: FastAPI request object.
        message: The message to display.
        category: Message category (success, error, warning, info).
    """
    try:
        if "flash_messages" not in request.session:
            request.session["flash_messages"] = []
        request.session["flash_messages"].append({
            "message": message,
            "category": category,
        })
    except (AssertionError, KeyError):
        # Session middleware not available, silently ignore
        pass


def get_flash_messages(request: Request) -> list[dict]:
    """Get and clear all flash messages from the session.

    Args:
        request: FastAPI request object.

    Returns:
        List of flash message dicts with 'message' and 'category' keys.
    """
    try:
        messages = request.session.pop("flash_messages", [])
        return messages
    except (AssertionError, KeyError):
        # Session middleware not available or session not initialized
        return []


def flash_template_response(
    templates: Jinja2Templates,
    request: Request,
    template_name: str,
    context: dict[str, Any],
    status_code: int = 200,
):
    """Create a template response with flash messages included.

    Args:
        templates: Jinja2Templates instance.
        request: FastAPI request object.
        template_name: Name of the template to render.
        context: Template context dict (must include 'request').
        status_code: HTTP status code.

    Returns:
        TemplateResponse with flash messages in context.
    """
    # Add flash messages to context
    context["flash_messages"] = get_flash_messages(request)
    return templates.TemplateResponse(
        template_name,
        context,
        status_code=status_code,
    )
