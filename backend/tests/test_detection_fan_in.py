"""Unit and integration tests for Multiple-Source Fan-In detection rule."""

import sqlite3
from pathlib import Path
from typing import Generator

import pytest
from app.db.migrations import run_migrations
from app.detection.registry import registry
from app.detection.rules.multi_source_fan_in import (
    MultipleIncomingSourcesRule,
    MultiSourceFanInRule,
)
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


def _seed_base_accounts_and_devices(conn: sqlite3.Connection, account_ids: list[str]) -> None:
    """Helper to insert test accounts and devices."""
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO devices (device_id) VALUES ('DEV001');")
    for acc_id in account_ids:
        cur.execute(
            "INSERT OR IGNORE INTO accounts "
            "(account_id, holder_name, vpa, bank, raw_created_at, created_at_utc) "
            "VALUES (?, ?, ?, 'TESTBANK', '2026-09-01T00:00:00+00:00', "
            "'2026-09-01T00:00:00+00:00');",
            (acc_id, f"Holder {acc_id}", f"{acc_id.lower()}@bank"),
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


# -----------------------------------------------------------------------------
# 1. Ground Truth Tests (S03_MANY_SOURCES and S04_CHARITY_COLLECTION)
# -----------------------------------------------------------------------------


def test_ground_truth_s03_many_sources_triggers(
    populated_shivam_db: sqlite3.Connection,
) -> None:
    """Verify S03_MANY_SOURCES triggers multiple_incoming_sources rule."""
    rule = MultipleIncomingSourcesRule()
    alerts = rule.detect(populated_shivam_db)

    # Find the alert for ACC0030
    s03_alert = next((a for a in alerts if a.account_ids[0] == "ACC0030"), None)
    assert s03_alert is not None, "S03_MANY_SOURCES was not detected on ACC0030"

    assert s03_alert.rule_id == "multiple_incoming_sources"
    assert len(s03_alert.account_ids) == 31  # 1 collector + 30 senders
    assert s03_alert.account_ids[0] == "ACC0030"
    assert len(s03_alert.txn_ids) == 30

    # Verify expected transactions range
    assert s03_alert.txn_ids[0] == "TXN002489"
    assert s03_alert.txn_ids[-1] == "TXN002543"

    # Evidence verification
    ev = s03_alert.evidence
    assert ev["distinct_sender_count"] == 30
    assert ev["transaction_count"] == 30
    assert 59000.0 <= ev["total_amount_inr"] <= 61000.0
    assert ev["duration_hours"] <= 3.0
    assert s03_alert.score >= 70.0
    assert s03_alert.priority in ("HIGH", "CRITICAL")
    assert s03_alert.graph_context is not None
    assert len(s03_alert.graph_context["nodes"]) == 31
    assert len(s03_alert.graph_context["edges"]) == 30


def test_ground_truth_s04_charity_collection_does_not_trigger(
    populated_shivam_db: sqlite3.Connection,
) -> None:
    """Verify S04_CHARITY_COLLECTION (spread over 5 days) does NOT trigger."""
    rule = MultipleIncomingSourcesRule()
    alerts = rule.detect(populated_shivam_db)

    # ACC0070 is the charity fundraiser account
    acc0070_alerts = [a for a in alerts if "ACC0070" in a.account_ids]
    assert len(acc0070_alerts) == 0, (
        f"False positive: S04_CHARITY_COLLECTION account ACC0070 was flagged: {acc0070_alerts}"
    )


# -----------------------------------------------------------------------------
# 2. Registry Integration Tests
# -----------------------------------------------------------------------------


def test_registry_registration_and_aliases(
    populated_shivam_db: sqlite3.Connection,
) -> None:
    """Verify rule is registered and accessible via canonical ID and aliases."""
    rule_canonical = registry.get("multiple_incoming_sources")
    assert rule_canonical is not None
    assert isinstance(rule_canonical, MultipleIncomingSourcesRule)

    # Upper case
    assert registry.get("MULTIPLE_INCOMING_SOURCES") is rule_canonical

    # Alias check
    rule_alias = registry.get("multiple_source_fan_in")
    assert rule_alias is rule_canonical
    assert registry.get("MULTIPLE_SOURCE_FAN_IN") is rule_canonical

    # Execution via run_rule
    alerts = registry.run_rule("multiple_incoming_sources", populated_shivam_db)
    assert any(a.account_ids[0] == "ACC0030" for a in alerts)


def test_custom_registry_and_run_all(populated_shivam_db: sqlite3.Connection) -> None:
    """Verify registry run_all executes all rules without duplicate runs."""
    all_rules = registry.list_rules()
    assert len(all_rules) == 3  # Rapid transfer, cycle, and fan-in

    all_alerts = registry.run_all(populated_shivam_db)
    rule_ids = {a.rule_id for a in all_alerts}
    assert "RAPID_ONWARD_TRANSFER" in rule_ids
    assert "TRANSACTION_CYCLE" in rule_ids
    assert "multiple_incoming_sources" in rule_ids


def test_rule_alias_class() -> None:
    """Verify MultiSourceFanInRule alias class behaves identically."""
    assert MultiSourceFanInRule is MultipleIncomingSourcesRule


# -----------------------------------------------------------------------------
# 3. Behavioral and Edge-Case Tests (Isolated SQLite)
# -----------------------------------------------------------------------------


def test_boundary_timestamps(empty_db: sqlite3.Connection) -> None:
    """Verify transactions within window alert, transactions beyond window do not."""
    accounts = [f"SRC{i:02d}" for i in range(1, 11)] + ["COLLECTOR"]
    _seed_base_accounts_and_devices(empty_db, accounts)

    # 10 senders over 2.5 hours (within default 3.0h window)
    for i, src in enumerate(accounts[:10]):
        minute = i * 15  # 0, 15, 30 ... 135 mins = 2.25 hours
        hour = minute // 60
        m = minute % 60
        ts = f"2026-09-01T{10+hour:02d}:{m:02d}:00+00:00"
        _insert_txn(empty_db, f"TXN_{i}", src, "COLLECTOR", 1500.0, ts)

    rule = MultipleIncomingSourcesRule()
    alerts = rule.detect(empty_db)
    assert len(alerts) == 1
    assert alerts[0].evidence["distinct_sender_count"] == 10


def test_window_exceeded_does_not_alert(empty_db: sqlite3.Connection) -> None:
    """Verify senders spread over 5 hours (> 3.0h) do not alert under default config."""
    accounts = [f"SRC{i:02d}" for i in range(1, 11)] + ["COLLECTOR"]
    _seed_base_accounts_and_devices(empty_db, accounts)

    # 10 senders spread over 5 hours (1 payment every 30 mins -> at most 6 per 3h window)
    for i, src in enumerate(accounts[:10]):
        minute = i * 32  # 0, 32, 64 ... 288 mins = 4.8 hours
        hour = minute // 60
        m = minute % 60
        ts = f"2026-09-01T{10+hour:02d}:{m:02d}:00+00:00"
        _insert_txn(empty_db, f"TXN_{i}", src, "COLLECTOR", 1500.0, ts)

    rule = MultipleIncomingSourcesRule()
    alerts_default = rule.detect(empty_db)
    assert len(alerts_default) == 0

    # With extended 6-hour window, it alerts
    alerts_extended = rule.detect(empty_db, config={"time_window_hours": 6.0})
    assert len(alerts_extended) == 1


def test_repeated_payments_by_one_sender_not_flagged(empty_db: sqlite3.Connection) -> None:
    """Verify multiple payments from the SAME sender do not count as distinct senders."""
    accounts = ["SENDER_ALONE", "COLLECTOR"]
    _seed_base_accounts_and_devices(empty_db, accounts)

    # 20 transactions from SENDER_ALONE to COLLECTOR in 30 minutes
    for i in range(20):
        ts = f"2026-09-01T10:{i:02d}:00+00:00"
        _insert_txn(empty_db, f"TXN_{i}", "SENDER_ALONE", "COLLECTOR", 2000.0, ts)

    rule = MultipleIncomingSourcesRule()
    alerts = rule.detect(empty_db)
    assert len(alerts) == 0  # Only 1 distinct sender (< 10)


def test_failed_transactions_excluded(empty_db: sqlite3.Connection) -> None:
    """Verify that failed or pending transactions are excluded from sender counts."""
    accounts = [f"SRC{i:02d}" for i in range(1, 13)] + ["COLLECTOR"]
    _seed_base_accounts_and_devices(empty_db, accounts)

    # 6 SUCCESS and 6 FAILED transactions within 1 hour
    for i, src in enumerate(accounts[:12]):
        st = "SUCCESS" if i < 6 else "FAILED"
        ts = f"2026-09-01T10:{i*4:02d}:00+00:00"
        _insert_txn(empty_db, f"TXN_{i}", src, "COLLECTOR", 2000.0, ts, status=st)

    rule = MultipleIncomingSourcesRule()
    alerts = rule.detect(empty_db)
    # Only 6 SUCCESS senders (< 10)
    assert len(alerts) == 0


def test_empty_input(empty_db: sqlite3.Connection) -> None:
    """Verify empty database returns empty alert list safely."""
    rule = MultipleIncomingSourcesRule()
    alerts = rule.detect(empty_db)
    assert alerts == []


def test_idempotent_execution_produces_identical_alerts(
    populated_shivam_db: sqlite3.Connection,
) -> None:
    """Verify repeated execution produces deterministic alert IDs and identical results."""
    rule = MultipleIncomingSourcesRule()
    run1 = rule.detect(populated_shivam_db)
    run2 = rule.detect(populated_shivam_db)

    assert len(run1) == len(run2)
    for a1, a2 in zip(run1, run2):
        assert a1.alert_id == a2.alert_id
        assert a1.account_ids == a2.account_ids
        assert a1.txn_ids == a2.txn_ids
        assert a1.score == a2.score
        assert a1.evidence == a2.evidence
