"""Unit tests for /api/ready endpoint."""

from unittest.mock import patch

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_ready_endpoint_database_connected():
    """Verify /api/ready returns 200 and ready status when database check succeeds."""
    with patch("app.api.routes.ready.check_connection") as mock_check:
        mock_check.return_value = (True, "Database connection successful")

        response = client.get("/api/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["database"]["connected"] is True
        assert data["database"]["message"] == "Database connection successful"
        assert "environment" in data


def test_ready_endpoint_database_not_connected():
    """Verify /api/ready returns 503 and not_ready status when database check fails."""
    with patch("app.api.routes.ready.check_connection") as mock_check:
        mock_check.return_value = (False, "TURSO_DATABASE_URL is not configured")

        response = client.get("/api/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "not_ready"
        assert data["database"]["connected"] is False
        assert data["database"]["message"] == "TURSO_DATABASE_URL is not configured"
        assert "environment" in data


def test_health_remains_healthy_when_database_is_not_ready():
    """Verify /api/health is completely decoupled from database status."""
    with patch("app.api.routes.ready.check_connection") as mock_check:
        mock_check.return_value = (False, "TURSO_DATABASE_URL is not configured")

        health_response = client.get("/api/health")
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "healthy"
