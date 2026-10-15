"""Unit and integration tests for the Transaction Cycle detection rule."""

import sqlite3
from pathlib import Path
from typing import Generator

import pytest
from app.db.migrations import run_migrations
from app.detection.registry import RuleRegistry, registry
from app.detection.rules.transaction_cycle import TransactionCycleRule
from app.services.importer import import_source_dataset


@pytest.fixture
def empty_db() -> Generator[sqlite3.Connection, None, None]:
    """Provide an in-memory SQLite database initialized with schema migrations."""
    conn = sqlite3.connect(":memory:")
    run_migrations(conn)
    yield conn
    conn.close()


@pytest.fixture
def populated_shivam_db() -> Generator[sqlite3.Connection, None, None]:
    """Provide an in-memory database imported with real synthetic incoming dataset."""
    real_data_dir = Path("backend/data/incoming")
    if not (real_data_dir / "accounts.csv").exists():
        pytest.skip("backend/data/incoming/ not present in local workspace")

    conn = sqlite3.connect(":memory:")
    run_migrations(conn)
    import_source_dataset(data_dir=real_data_dir, conn=conn)
    yield conn
    conn.close()


# -----------------------------------------------------------------------------
# 1. Ground Truth Tests (S05_CYCLE and S06_ROOMMATE_SETTLEUP)
# -----------------------------------------------------------------------------


def test_ground_truth_s05_cycle_triggers(
    populated_shivam_db: sqlite3.Connection,
) -> None:
    """Verify S05_CYCLE triggers TRANSACTION_CYCLE with exact accounts and txns."""
    rule = TransactionCycleRule()
    alerts = rule.detect(populated_shivam_db)

    # Find the alert corresponding to S05
    s05_alert = next(
        (a for a in alerts if "ACC0101" in a.account_ids and "ACC0102" in a.account_ids),
        None,
    )
    assert s05_alert is not None, "S05_CYCLE was not detected by TransactionCycleRule"

    expected_accounts = ["ACC0101", "ACC0102", "ACC0103"]
    expected_txns = ["TXN002702", "TXN002703", "TXN002705"]

    assert s05_alert.account_ids == expected_accounts
    assert s05_alert.txn_ids == expected_txns
    assert s05_alert.rule_id == "TRANSACTION_CYCLE"
    assert s05_alert.evidence["cycle_length"] == 3
    assert s05_alert.evidence["start_amount_inr"] == 25000.0
    assert s05_alert.evidence["end_amount_inr"] == 24502.5
    assert s05_alert.evidence["amount_retention_percentage"] == 98.01
    assert s05_alert.evidence["duration_minutes"] == 41.0
    assert s05_alert.score >= 70.0
    assert s05_alert.graph_context is not None
    assert len(s05_alert.graph_context["nodes"]) == 3
    assert len(s05_alert.graph_context["edges"]) == 3


def test_ground_truth_s06_roommate_settleup_does_not_trigger(
    populated_shivam_db: sqlite3.Connection,
) -> None:
    """Verify S06_ROOMMATE_SETTLEUP does NOT trigger TRANSACTION_CYCLE."""
    rule = TransactionCycleRule()
    alerts = rule.detect(populated_shivam_db)

    # Ensure no alert contains any roommate settleup account
    s06_accounts = {"ACC0111", "ACC0112", "ACC0113"}
    s06_txns = {"TXN001076", "TXN001305", "TXN001511"}

    for alert in alerts:
        flagged_accs = set(alert.account_ids)
        flagged_txns = set(alert.txn_ids)
        assert not (s06_accounts & flagged_accs), (
            f"False positive: Roommate settleup accounts {flagged_accs} alerted!"
        )
        assert not (s06_txns & flagged_txns), (
            f"False positive: Roommate settleup txns {flagged_txns} alerted!"
        )


# -----------------------------------------------------------------------------
# 2. Registry Integration Tests
# -----------------------------------------------------------------------------


def test_registry_registration_and_execution(
    populated_shivam_db: sqlite3.Connection,
) -> None:
    """Verify TransactionCycleRule is registered in default registry and runs via run_rule."""
    rule = registry.get("TRANSACTION_CYCLE")
    assert rule is not None
    assert isinstance(rule, TransactionCycleRule)

    # Case-insensitivity check
    rule_lower = registry.get("transaction_cycle")
    assert rule_lower is rule

    # Execution via registry
    alerts = registry.run_rule("TRANSACTION_CYCLE", populated_shivam_db)
    assert any("ACC0101" in a.account_ids for a in alerts)


def test_custom_registry_instance() -> None:
    """Verify isolated custom RuleRegistry works independently."""
    custom_reg = RuleRegistry()
    cycle_rule = TransactionCycleRule()
    custom_reg.register(cycle_rule)

    assert custom_reg.get("TRANSACTION_CYCLE") is cycle_rule
    assert len(custom_reg.list_rules()) == 1


# -----------------------------------------------------------------------------
# 3. Behavioral and Edge-Case Tests (Isolated SQLite)
# -----------------------------------------------------------------------------


def _seed_base_accounts_and_devices(conn: sqlite3.Connection) -> None:
    """Helper to insert base accounts and devices for synthetic scenario tests."""
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO devices (device_id) VALUES ('DEV001');")
    for acc_id, vpa in [
        ("A", "a@bank"),
        ("B", "b@bank"),
        ("C", "c@bank"),
        ("D", "d@bank"),
    ]:
        cur.execute(
            "INSERT OR IGNORE INTO accounts "
            "(account_id, holder_name, vpa, bank, raw_created_at, created_at_utc) "
            "VALUES (?, ?, ?, 'TESTBANK', '2026-09-01T00:00:00+00:00', "
            "'2026-09-01T00:00:00+00:00');",
            (acc_id, f"Holder {acc_id}", vpa),
        )
    conn.commit()
    cur.close()


def _insert_txn(
    conn: sqlite3.Connection,
    txn_id: str,
    sender: str,
    receiver: str,
    amount_inr: float,
    ts: str,
    status: str = "SUCCESS",
) -> None:
    """Helper to insert a test transaction row cleanly."""
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO transactions "
        "(txn_id, sender_account_id, receiver_account_id, sender_vpa, receiver_vpa, "
        "amount_paise, amount_inr, raw_timestamp, timestamp_utc, txn_type, status, device_id) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'P2P', ?, 'DEV001');",
        (
            txn_id,
            sender,
            receiver,
            f"{sender.lower()}@bank",
            f"{receiver.lower()}@bank",
            int(amount_inr * 100),
            amount_inr,
            ts,
            ts,
            status,
        ),
    )
    conn.commit()
    cur.close()


def test_canonical_deduplication(empty_db: sqlite3.Connection) -> None:
    """Verify cycle detection does not generate duplicate alerts for different start nodes."""
    _seed_base_accounts_and_devices(empty_db)
    _insert_txn(empty_db, "T1", "A", "B", 5000.0, "2026-09-01T10:00:00+00:00")
    _insert_txn(empty_db, "T2", "B", "C", 4900.0, "2026-09-01T10:15:00+00:00")
    _insert_txn(empty_db, "T3", "C", "A", 4800.0, "2026-09-01T10:30:00+00:00")

    rule = TransactionCycleRule()
    alerts = rule.detect(empty_db)
    assert len(alerts) == 1, f"Expected exactly 1 alert after deduplication, got {len(alerts)}"
    assert alerts[0].txn_ids == ["T1", "T2", "T3"]


def test_time_window_boundary(empty_db: sqlite3.Connection) -> None:
    """Verify transactions exceeding max_duration_hours do not alert."""
    _seed_base_accounts_and_devices(empty_db)
    # Cycle spanning 5.5 hours (exceeds default 4.0h limit)
    _insert_txn(empty_db, "T1", "A", "B", 5000.0, "2026-09-01T10:00:00+00:00")
    _insert_txn(empty_db, "T2", "B", "C", 4900.0, "2026-09-01T12:00:00+00:00")
    _insert_txn(empty_db, "T3", "C", "A", 4800.0, "2026-09-01T15:30:00+00:00")

    rule = TransactionCycleRule()
    # Default 4h should find no cycle
    alerts_default = rule.detect(empty_db)
    assert len(alerts_default) == 0

    # Overridden 6h should detect the cycle
    alerts_extended = rule.detect(empty_db, config={"max_duration_hours": 6.0})
    assert len(alerts_extended) == 1


def test_amount_retention_ratio_boundary(empty_db: sqlite3.Connection) -> None:
    """Verify hops with severe amount drop-off (< min_amount_ratio) do not trigger."""
    _seed_base_accounts_and_devices(empty_db)
    # Hop B -> C only forwards 2,000 out of 5,000 (ratio 0.40 < default 0.70)
    _insert_txn(empty_db, "T1", "A", "B", 5000.0, "2026-09-01T10:00:00+00:00")
    _insert_txn(empty_db, "T2", "B", "C", 2000.0, "2026-09-01T10:15:00+00:00")
    _insert_txn(empty_db, "T3", "C", "A", 1900.0, "2026-09-01T10:30:00+00:00")

    rule = TransactionCycleRule()
    alerts = rule.detect(empty_db)
    assert len(alerts) == 0


def test_failed_transactions_do_not_alert(empty_db: sqlite3.Connection) -> None:
    """Verify that failed or pending transactions cannot form a valid cycle."""
    _seed_base_accounts_and_devices(empty_db)
    # Hop B -> C is FAILED
    _insert_txn(empty_db, "T1", "A", "B", 5000.0, "2026-09-01T10:00:00+00:00", "SUCCESS")
    _insert_txn(empty_db, "T2", "B", "C", 4900.0, "2026-09-01T10:15:00+00:00", "FAILED")
    _insert_txn(empty_db, "T3", "C", "A", 4800.0, "2026-09-01T10:30:00+00:00", "SUCCESS")

    rule = TransactionCycleRule()
    alerts = rule.detect(empty_db)
    assert len(alerts) == 0


def test_two_node_reciprocal_is_not_cycle(empty_db: sqlite3.Connection) -> None:
    """Verify 2-node reciprocal ping-pong (A -> B -> A) does not trigger cycle alert."""
    _seed_base_accounts_and_devices(empty_db)
    _insert_txn(empty_db, "T1", "A", "B", 5000.0, "2026-09-01T10:00:00+00:00")
    _insert_txn(empty_db, "T2", "B", "A", 5000.0, "2026-09-01T10:15:00+00:00")

    rule = TransactionCycleRule()
    alerts = rule.detect(empty_db)
    assert len(alerts) == 0


def test_idempotent_execution_produces_identical_alerts(
    populated_shivam_db: sqlite3.Connection,
) -> None:
    """Verify repeated detection runs produce deterministic alert IDs and identical payloads."""
    rule = TransactionCycleRule()
    run1 = rule.detect(populated_shivam_db)
    run2 = rule.detect(populated_shivam_db)

    assert len(run1) == len(run2)
    for a1, a2 in zip(run1, run2):
        assert a1.alert_id == a2.alert_id
        assert a1.account_ids == a2.account_ids
        assert a1.txn_ids == a2.txn_ids
        assert a1.score == a2.score
