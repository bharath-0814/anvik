"""Unit tests for the preloaded complaints API endpoint and CORS headers."""

import sqlite3
from unittest.mock import patch

import pytest
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def test_client() -> TestClient:
    """Create a FastAPI test client."""
    return TestClient(app)


def test_cors_headers_on_options_request(test_client: TestClient) -> None:
    """Verify that CORS preflight request returns expected headers for production frontend."""
    headers = {
        "Origin": "https://anvik-frontend-alpha.vercel.app",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "authorization,content-type",
    }
    response = test_client.options("/api/graph", headers=headers)
    assert response.status_code == 200
    assert (
        response.headers.get("access-control-allow-origin")
        == "https://anvik-frontend-alpha.vercel.app"
    )
    assert "GET" in response.headers.get("access-control-allow-methods", "")


def test_cors_headers_on_vercel_preview_domain(test_client: TestClient) -> None:
    """Verify that CORS works for arbitrary Vercel preview deployment URLs matching regex."""
    headers = {
        "Origin": "https://anvik-frontend-mf6xa01vu-bharathg0814-3022s-projects.vercel.app",
        "Access-Control-Request-Method": "GET",
    }
    response = test_client.options("/api/health", headers=headers)
    assert response.status_code == 200
    assert (
        response.headers.get("access-control-allow-origin")
        == "https://anvik-frontend-mf6xa01vu-bharathg0814-3022s-projects.vercel.app"
    )


def test_get_complaints_db_unavailable(test_client: TestClient) -> None:
    """Verify 503 response when Turso database connection is unavailable."""
    with patch(
        "app.api.routes.complaints.get_turso_connection",
        side_effect=ValueError("DB unavailable"),
    ):
        response = test_client.get("/api/complaints")
        assert response.status_code == 503
        assert "Database connection unavailable" in response.json()["detail"]


def test_get_complaints_success(test_client: TestClient) -> None:
    """Verify complaints endpoint returns formatted records from SQLite in-memory database."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE accounts ("
        "account_id TEXT PRIMARY KEY, holder_name TEXT, vpa TEXT, bank TEXT, created_at TEXT)"
    )
    cur.execute("CREATE TABLE devices (device_id TEXT PRIMARY KEY, account_id TEXT)")
    cur.execute(
        "CREATE TABLE transactions ("
        "txn_id TEXT PRIMARY KEY, sender_account_id TEXT, receiver_account_id TEXT, "
        "sender_vpa TEXT, receiver_vpa TEXT, amount_paise INT, amount_inr REAL, "
        "raw_timestamp TEXT, timestamp_utc TEXT, txn_type TEXT, status TEXT, device_id TEXT)"
    )
    cur.execute(
        "CREATE TABLE complaints ("
        "complaint_id TEXT PRIMARY KEY, victim_account_id TEXT, victim_vpa TEXT, "
        "txn_id TEXT, raw_complaint_date TEXT, complaint_date_utc TEXT)"
    )

    cur.execute(
        "INSERT INTO accounts VALUES ('ACC001', 'Alice', 'alice@bank', 'HDFC', '2026-01-01')"
    )
    cur.execute("INSERT INTO accounts VALUES ('ACC002', 'Bob', 'bob@bank', 'SBI', '2026-01-01')")
    cur.execute("INSERT INTO devices VALUES ('DEV001', 'ACC001')")
    cur.execute(
        "INSERT INTO transactions VALUES ("
        "'TXN101', 'ACC001', 'ACC002', 'alice@bank', 'bob@bank', 500000, 5000.0, "
        "'2026-09-01 10:00:00', '2026-09-01T04:30:00Z', 'PAY', 'SUCCESS', 'DEV001')"
    )
    cur.execute(
        "INSERT INTO complaints VALUES ("
        "'CMP001', 'ACC001', 'alice@bank', 'TXN101', '2026-09-02', '2026-09-02T00:00:00Z')"
    )
    conn.commit()

    with patch("app.api.routes.complaints.get_turso_connection", return_value=conn):
        response = test_client.get("/api/complaints")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert len(data["complaints"]) == 1
        item = data["complaints"][0]
        assert item["complaint_id"] == "CMP001"
        assert item["victim_account_id"] == "ACC001"
        assert item["victim_vpa"] == "alice@bank"
        assert item["txn_id"] == "TXN101"
        assert item["amount_inr"] == 5000.0
        assert item["beneficiary_account_id"] == "ACC002"
        assert item["beneficiary_vpa"] == "bob@bank"
        assert item["complaint_date"] == "2026-09-02T00:00:00Z"
        assert item["status"] == "UNDER_INVESTIGATION"


def test_get_complaints_filter_by_account_id(test_client: TestClient) -> None:
    """Verify complaints endpoint filters correctly by victim account_id."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE accounts ("
        "account_id TEXT PRIMARY KEY, holder_name TEXT, vpa TEXT, bank TEXT, created_at TEXT)"
    )
    cur.execute(
        "CREATE TABLE transactions ("
        "txn_id TEXT PRIMARY KEY, sender_account_id TEXT, receiver_account_id TEXT, "
        "sender_vpa TEXT, receiver_vpa TEXT, amount_paise INT, amount_inr REAL, "
        "raw_timestamp TEXT, timestamp_utc TEXT, txn_type TEXT, status TEXT, device_id TEXT)"
    )
    cur.execute(
        "CREATE TABLE complaints ("
        "complaint_id TEXT PRIMARY KEY, victim_account_id TEXT, victim_vpa TEXT, "
        "txn_id TEXT, raw_complaint_date TEXT, complaint_date_utc TEXT)"
    )

    cur.execute(
        "INSERT INTO complaints VALUES ("
        "'CMP001', 'ACC001', 'alice@bank', 'TXN101', '2026-09-02', '2026-09-02')"
    )
    cur.execute(
        "INSERT INTO complaints VALUES ("
        "'CMP002', 'ACC002', 'bob@bank', 'TXN102', '2026-09-03', '2026-09-03')"
    )
    conn.commit()

    with patch("app.api.routes.complaints.get_turso_connection", return_value=conn):
        response = test_client.get("/api/complaints?account_id=ACC001")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert data["complaints"][0]["victim_account_id"] == "ACC001"
