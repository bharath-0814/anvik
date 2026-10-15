"""Tests for health check endpoint."""

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health_check() -> None:
    """Test that the /api/health endpoint returns 200 and healthy status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("status") == "healthy"
    assert payload.get("service") == "anvik-backend"
