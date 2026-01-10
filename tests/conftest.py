"""Pytest configuration and fixtures."""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment before importing app modules
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ENVIRONMENT"] = "development"

from app.database.session import Base, get_db
from app.main import app


# Create test engine with SQLite in-memory
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


def override_get_db():
    """Override database dependency for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def test_app():
    """Create test application instance."""
    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    # Import models to register them with metadata
    from app.models import (  # noqa: F401
        User,
        Project,
        Experiment,
        Replicate,
        Todo,
        Note,
        ActivityLog,
        Session,
    )

    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(test_app, db_session):
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
