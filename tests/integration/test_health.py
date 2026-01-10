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

    def test_root_returns_200(self, client):
        """Root endpoint should return 200 OK."""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_returns_welcome_message(self, client):
        """Root endpoint should return welcome message."""
        response = client.get("/")
        data = response.json()
        assert "message" in data
        assert "Lab Tracker" in data["message"]
