"""Pytest configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def test_app():
    """Create test application instance."""
    return app


@pytest.fixture(scope="function")
def client(test_app):
    """Create test client for each test function."""
    with TestClient(test_app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def authenticated_client(client):
    """Create authenticated test client.

    Will be implemented when auth is added.
    For now, returns regular client.
    """
    # TODO: Add authentication when auth slice is implemented
    return client
