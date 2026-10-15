"""Unit tests for Turso SQLite schema migrations and constraints."""

import sqlite3

import pytest
from app.db.migrations import get_applied_migrations, run_migrations


@pytest.fixture
def memory_db() -> sqlite3.Connection:
    """Provide an in-memory SQLite database connection."""
    conn = sqlite3.connect(":memory:")
    yield conn
    conn.close()


def test_migrations_create_expected_tables(memory_db: sqlite3.Connection) -> None:
    """Verify migrations create all required tables."""
    applied = run_migrations(memory_db)
    assert "001" in applied

    cursor = memory_db.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
    )
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()

    expected_tables = [
        "account_devices",
        "accounts",
        "complaints",
        "dataset_imports",
        "devices",
        "schema_migrations",
        "transactions",
    ]
    for table in expected_tables:
        assert table in tables


def test_migrations_create_expected_indexes(memory_db: sqlite3.Connection) -> None:
    """Verify performance indexes are created."""
    run_migrations(memory_db)

    cursor = memory_db.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_autoindex%';"
    )
    indexes = [row[0] for row in cursor.fetchall()]
    cursor.close()

    expected_indexes = [
        "idx_accounts_vpa",
        "idx_txns_sender_acc",
        "idx_txns_receiver_acc",
        "idx_txns_timestamp_utc",
        "idx_txns_status_type",
        "idx_txns_device",
        "idx_complaints_txn",
        "idx_complaints_victim_acc",
        "idx_acc_devices_dev",
    ]
    for idx in expected_indexes:
        assert idx in indexes


def test_migration_runner_is_idempotent(memory_db: sqlite3.Connection) -> None:
    """Verify running migrations multiple times is a safe no-op."""
    first_run = run_migrations(memory_db)
    assert len(first_run) == 1

    second_run = run_migrations(memory_db)
    assert len(second_run) == 0

    applied = get_applied_migrations(memory_db)
    assert "001" in applied


def test_primary_key_constraints(memory_db: sqlite3.Connection) -> None:
    """Verify primary key uniqueness enforcement."""
    run_migrations(memory_db)
    cursor = memory_db.cursor()

    # Accounts PK
    cursor.execute(
        "INSERT INTO accounts (account_id, holder_name, vpa, bank, raw_created_at, created_at_utc) "
        "VALUES ('ACC0001', 'Test User', 'test@upi', 'HDFC', "
        "'2026-09-01 10:00:00', '2026-09-01T04:30:00+00:00');"
    )
    memory_db.commit()

    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            "INSERT INTO accounts (account_id, holder_name, vpa, bank, "
            "raw_created_at, created_at_utc) "
            "VALUES ('ACC0001', 'Duplicate', 'dup@upi', 'SBI', "
            "'2026-09-01 10:00:00', '2026-09-01T04:30:00+00:00');"
        )

    # Devices PK
    cursor.execute("INSERT INTO devices (device_id) VALUES ('DEV0001');")
    memory_db.commit()

    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("INSERT INTO devices (device_id) VALUES ('DEV0001');")

    cursor.close()
