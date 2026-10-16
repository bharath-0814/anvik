"""Unit tests for transaction repository and API endpoints."""

import sqlite3
from unittest.mock import patch

import pytest
from app.db.repository import get_transaction_by_id
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def test_client() -> TestClient:
    """Create a FastAPI test client."""
    return TestClient(app)


def _create_test_db() -> sqlite3.Connection:
    """Create an in-memory SQLite database populated with a test transaction."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE transactions ("
        "txn_id TEXT PRIMARY KEY, sender_account_id TEXT, receiver_account_id TEXT, "
        "sender_vpa TEXT, receiver_vpa TEXT, amount_paise INT, amount_inr REAL, "
        "raw_timestamp TEXT, timestamp_utc TEXT, txn_type TEXT, status TEXT, device_id TEXT)"
    )
    cur.execute(
        "INSERT INTO transactions VALUES ("
        "'TXN101', 'ACC001', 'ACC002', 'alice@bank', 'bob@bank', 500000, 5000.0, "
        "'2026-09-01 10:00:00', '2026-09-01T04:30:00Z', 'PAY', 'SUCCESS', 'DEV001')"
    )
    conn.commit()
    return conn


def test_repository_get_transaction_by_id() -> None:
    """Verify repository get_transaction_by_id returns dict or None."""
    conn = _create_test_db()

    txn = get_transaction_by_id(conn, "TXN101")
    assert txn is not None
    assert txn["txn_id"] == "TXN101"
    assert txn["sender_account_id"] == "ACC001"
    assert txn["receiver_account_id"] == "ACC002"
    assert txn["sender_vpa"] == "alice@bank"
    assert txn["receiver_vpa"] == "bob@bank"
    assert txn["amount_paise"] == 500000
    assert txn["amount_inr"] == 5000.0
    assert txn["raw_timestamp"] == "2026-09-01 10:00:00"
    assert txn["timestamp_utc"] == "2026-09-01T04:30:00Z"
    assert txn["txn_type"] == "PAY"
    assert txn["status"] == "SUCCESS"
    assert txn["device_id"] == "DEV001"

    missing = get_transaction_by_id(conn, "TXN999")
    assert missing is None
    conn.close()


def test_get_transaction_success(test_client: TestClient) -> None:
    """Verify GET /api/transactions/{txn_id} returns 200 OK for an existing transaction."""
    with patch("app.api.routes.transactions.get_turso_connection", side_effect=_create_test_db):
        response = test_client.get("/api/transactions/TXN101")
        assert response.status_code == 200
        data = response.json()
        assert data["txn_id"] == "TXN101"
        assert data["sender_account_id"] == "ACC001"
        assert data["receiver_account_id"] == "ACC002"
        assert data["sender_vpa"] == "alice@bank"
        assert data["receiver_vpa"] == "bob@bank"
        assert data["amount_paise"] == 500000
        assert data["amount_inr"] == 5000.0
        assert data["raw_timestamp"] == "2026-09-01 10:00:00"
        assert data["timestamp_utc"] == "2026-09-01T04:30:00Z"
        assert data["txn_type"] == "PAY"
        assert data["status"] == "SUCCESS"
        assert data["device_id"] == "DEV001"

        # Also test dual-mounted route without /api prefix
        res_no_prefix = test_client.get("/transactions/TXN101")
        assert res_no_prefix.status_code == 200
        assert res_no_prefix.json()["txn_id"] == "TXN101"


def test_get_transaction_not_found(test_client: TestClient) -> None:
    """Verify GET /api/transactions/{txn_id} returns 404 for a non-existent transaction."""
    with patch("app.api.routes.transactions.get_turso_connection", side_effect=_create_test_db):
        response = test_client.get("/api/transactions/TXN_NONEXISTENT")
        assert response.status_code == 404
        assert response.json()["detail"] == "Transaction not found"


def test_get_transaction_db_unavailable(test_client: TestClient) -> None:
    """Verify 503 response when Turso database connection is unavailable."""
    with patch(
        "app.api.routes.transactions.get_turso_connection",
        side_effect=ValueError("DB unavailable"),
    ):
        response = test_client.get("/api/transactions/TXN101")
        assert response.status_code == 503
        assert "Database connection unavailable" in response.json()["detail"]
