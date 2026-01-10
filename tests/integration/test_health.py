"""Integration tests for health check endpoint."""

import pytest


class TestHealthCheck:
    """Tests for the /health endpoint."""

    def test_health_check_returns_200(self, client):
        """Health check should return 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_check_returns_healthy_status(self, client):
        """Health check should return healthy status."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_check_returns_version(self, client):
        """Health check should return application version."""
        response = client.get("/health")
        data = response.json()
        assert "version" in data
        assert data["version"] == "0.1.0"

    def test_health_check_returns_environment(self, client):
        """Health check should return environment."""
        response = client.get("/health")
        data = response.json()
        assert "environment" in data


class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_root_redirects_unauthenticated_to_login(self, client):
        """Root endpoint should redirect unauthenticated users to login."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers.get("location") == "/login"

    def test_root_shows_dashboard_after_following_redirect(self, client):
        """Root endpoint should eventually show login page."""
        response = client.get("/")  # follows redirects by default
        assert response.status_code == 200
        assert "Sign in" in response.text
