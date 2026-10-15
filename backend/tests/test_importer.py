"""Unit and integration tests for dataset importer service."""

import csv
import sqlite3
from pathlib import Path

import pytest
from app.db.migrations import run_migrations
from app.db.repository import (
    get_account_devices,
    get_accounts,
    get_complaints,
    get_devices,
    get_latest_import,
    get_transactions,
)
from app.services.importer import import_source_dataset


@pytest.fixture
def memory_db() -> sqlite3.Connection:
    """Provide an in-memory SQLite database initialized with current schema."""
    conn = sqlite3.connect(":memory:")
    run_migrations(conn)
    yield conn
    conn.close()


@pytest.fixture
def mock_dataset_dir(tmp_path: Path) -> Path:
    """Create a minimal valid synthetic dataset in a temporary directory."""
    # accounts.csv
    accounts_csv = tmp_path / "accounts.csv"
    with open(accounts_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["account_id", "holder_name", "vpa", "bank", "created_at"])
        writer.writerow(
            ["ACC0001", "Alice Smith", "alice@okhdfcbank", "HDFC", "2026-09-01 10:00:00"]
        )
        writer.writerow(["ACC0002", "Bob Jones", "bob@oksbi", "SBI", "2026-09-02 11:30:00"])

    # devices.csv
    devices_csv = tmp_path / "devices.csv"
    with open(devices_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["account_id", "device_id"])
        writer.writerow(["ACC0001", "DEV0001"])
        writer.writerow(["ACC0002", "DEV0002"])

    # transactions.csv
    txns_csv = tmp_path / "transactions.csv"
    with open(txns_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "txn_id",
            "sender_account_id",
            "receiver_account_id",
            "sender_vpa",
            "receiver_vpa",
            "amount",
            "timestamp",
            "txn_type",
            "status",
            "device_id",
        ])
        writer.writerow([
            "TXN0001",
            "ACC0001",
            "ACC0002",
            "alice@okhdfcbank",
            "bob@oksbi",
            "1250.75",
            "2026-09-03 14:00:00",
            "PAY",
            "SUCCESS",
            "DEV0001",
        ])
        writer.writerow([
            "TXN0002",
            "ACC0002",
            "ACC0001",
            "bob@oksbi",
            "alice@okhdfcbank",
            "50.00",
            "2026-09-03 15:00:00",
            "COLLECT",
            "FAILED",
            "DEV0002",
        ])

    # complaints.csv
    complaints_csv = tmp_path / "complaints.csv"
    with open(complaints_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["complaint_id", "victim_account_id", "victim_vpa", "txn_id", "complaint_date"]
        )
        writer.writerow(
            ["CMP0001", "ACC0001", "alice@okhdfcbank", "TXN0001", "2026-09-04 09:00:00"]
        )

    return tmp_path


def test_import_mock_dataset(memory_db: sqlite3.Connection, mock_dataset_dir: Path) -> None:
    """Verify clean import of mock dataset into memory DB."""
    result = import_source_dataset(data_dir=mock_dataset_dir, conn=memory_db)

    assert result.is_success is True
    assert result.is_noop is False
    assert result.account_count == 2
    assert result.device_count == 2
    assert result.account_device_count == 2
    assert result.transaction_count == 2
    assert result.complaint_count == 1

    # Verify accounts in DB
    accounts = get_accounts(memory_db)
    assert len(accounts) == 2
    assert accounts[0]["account_id"] == "ACC0001"
    assert accounts[0]["bank"] == "HDFC"

    # Verify devices
    devices = get_devices(memory_db)
    assert len(devices) == 2

    # Verify account_devices
    links = get_account_devices(memory_db)
    assert len(links) == 2

    # Verify transactions & decimal-safe paise conversion
    txns = get_transactions(memory_db)
    assert len(txns) == 2
    txn1 = next(t for t in txns if t["txn_id"] == "TXN0001")
    assert txn1["amount_paise"] == 125075
    assert txn1["amount_inr"] == 1250.75
    assert txn1["raw_timestamp"] == "2026-09-03 14:00:00"
    assert txn1["timestamp_utc"] == "2026-09-03T08:30:00+00:00"
    assert txn1["status"] == "SUCCESS"

    # Verify complaints
    complaints = get_complaints(memory_db)
    assert len(complaints) == 1
    assert complaints[0]["complaint_id"] == "CMP0001"

    # Verify dataset_imports record
    latest = get_latest_import(memory_db)
    assert latest is not None
    assert latest["account_count"] == 2
    assert latest["status"] == "SUCCESS"


def test_import_idempotency_noop(memory_db: sqlite3.Connection, mock_dataset_dir: Path) -> None:
    """Verify re-importing identical dataset without replace flag is a no-op."""
    first = import_source_dataset(data_dir=mock_dataset_dir, conn=memory_db)
    assert first.is_success is True
    assert first.is_noop is False

    second = import_source_dataset(data_dir=mock_dataset_dir, conn=memory_db)
    assert second.is_success is True
    assert second.is_noop is True
    assert second.data_hash == first.data_hash


def test_import_replace_existing(memory_db: sqlite3.Connection, mock_dataset_dir: Path) -> None:
    """Verify replace_existing clears existing tables and re-inserts."""
    first = import_source_dataset(data_dir=mock_dataset_dir, conn=memory_db)
    assert first.is_noop is False

    replaced = import_source_dataset(
        data_dir=mock_dataset_dir, conn=memory_db, replace_existing=True
    )
    assert replaced.is_success is True
    assert replaced.is_noop is False
    assert replaced.account_count == 2
    assert len(get_accounts(memory_db)) == 2


def test_import_fails_on_corrupt_dataset(memory_db: sqlite3.Connection, tmp_path: Path) -> None:
    """Verify validator rejection prevents database insertion."""
    bad_dir = tmp_path / "bad_data"
    bad_dir.mkdir()

    # Create transactions without accounts
    txns_csv = bad_dir / "transactions.csv"
    with open(txns_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["txn_id", "sender_account_id", "receiver_account_id", "amount", "timestamp", "status"]
        )
        writer.writerow(["TXN001", "ACC001", "ACC002", "100", "2026-09-01 10:00:00", "SUCCESS"])

    with pytest.raises(Exception):
        import_source_dataset(data_dir=bad_dir, conn=memory_db)

    # Confirm nothing was imported
    assert len(get_accounts(memory_db)) == 0


def test_real_synthetic_dataset_import_into_memory(memory_db: sqlite3.Connection) -> None:
    """Verify complete import of Shivam's real synthetic dataset if present."""
    real_data_dir = Path("backend/data/incoming")
    if not (real_data_dir / "accounts.csv").exists():
        pytest.skip("backend/data/incoming/ not present in local workspace")

    result = import_source_dataset(data_dir=real_data_dir, conn=memory_db)

    assert result.is_success is True
    assert result.account_count == 200
    assert result.device_count == 196
    assert result.account_device_count == 233
    assert result.transaction_count == 3129
    assert result.complaint_count == 10
