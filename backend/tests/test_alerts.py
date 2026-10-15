"""Unit tests for /api/alerts endpoint."""

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_get_alerts_endpoint():
    """Verify GET /api/alerts returns Aryan's contract schema with 24 alerts."""
    res = client.get("/api/alerts")
    assert res.status_code == 200
    data = res.json()

    assert "alerts" in data
    assert "rings" in data
    assert "account_summaries" in data
    assert "meta" in data

    assert data["count"] == 24
    assert len(data["alerts"]) == 24
    assert len(data["rings"]) == 1

    first_alert = data["alerts"][0]
    assert "alert_id" in first_alert
    assert "rule_id" in first_alert
    assert "priority" in first_alert
    assert "score" in first_alert
    assert "evidence" in first_alert
    assert "score_breakdown" in first_alert["evidence"]


def test_get_alerts_filter_by_rule():
    """Verify GET /api/alerts with rule_id filter."""
    res = client.get("/api/alerts?rule_id=RAPID_ONWARD_TRANSFER")
    assert res.status_code == 200
    data = res.json()

    assert data["count"] == 8
    for a in data["alerts"]:
        assert a["rule_id"] == "RAPID_ONWARD_TRANSFER"


def test_get_alerts_filter_by_priority():
    """Verify GET /api/alerts with priority filter."""
    res = client.get("/api/alerts?priority=high")
    assert res.status_code == 200
    data = res.json()

    assert data["count"] == 11
    for a in data["alerts"]:
        assert a["priority"] == "high"
