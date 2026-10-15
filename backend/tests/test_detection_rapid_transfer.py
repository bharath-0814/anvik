"""Unit and integration tests for the Rapid Onward Transfer detection rule and registry."""

import sqlite3
from pathlib import Path
from typing import Generator

import pytest
from app.db.migrations import run_migrations
from app.detection.registry import RuleRegistry, registry
from app.detection.rules.rapid_transfer import RapidOnwardTransferRule
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
# 1. Ground Truth Tests (S01_RAPID_CHAIN and S02_SHOP_SUPPLIER)
# -----------------------------------------------------------------------------


def test_ground_truth_s01_rapid_chain_triggers(
    populated_shivam_db: sqlite3.Connection,
) -> None:
    """Verify S01_RAPID_CHAIN triggers RAPID_ONWARD_TRANSFER with exact accounts and txns."""
    rule = RapidOnwardTransferRule()
    alerts = rule.detect(populated_shivam_db)

    # Find the alert corresponding to S01
    s01_alert = next(
        (a for a in alerts if "ACC0012" in a.account_ids and "ACC0013" in a.account_ids),
        None,
    )
    assert s01_alert is not None, "S01_RAPID_CHAIN was not detected by RapidOnwardTransferRule"

    # Verify accounts and transactions match ground truth
    expected_accounts = ["ACC0011", "ACC0012", "ACC0013", "ACC0014"]
    expected_txns = ["TXN001945", "TXN001946", "TXN001948"]

    assert s01_alert.account_ids == expected_accounts
    assert s01_alert.txn_ids == expected_txns
    assert s01_alert.rule_id == "RAPID_ONWARD_TRANSFER"
    assert s01_alert.priority in ("HIGH", "CRITICAL")
    assert s01_alert.evidence["hop_count"] == 2
    assert s01_alert.evidence["initial_amount_inr"] == 48000.0
    assert s01_alert.evidence["final_amount_inr"] == 43320.0
    assert s01_alert.evidence["overall_forwarding_percentage"] == 90.25

    # Verify explainability fields
    assert "ACC0011" in s01_alert.explanation
    assert "ACC0014" in s01_alert.explanation
    assert len(s01_alert.limitations) >= 2
    assert len(s01_alert.alternative_explanations) >= 2

    # Verify graph context
    assert s01_alert.graph_context is not None
    assert len(s01_alert.graph_context["nodes"]) == 4
    assert len(s01_alert.graph_context["edges"]) == 3


def test_ground_truth_s02_shop_supplier_does_not_trigger(
    populated_shivam_db: sqlite3.Connection,
) -> None:
    """Verify S02_SHOP_SUPPLIER does NOT trigger RAPID_ONWARD_TRANSFER."""
    rule = RapidOnwardTransferRule()
    alerts = rule.detect(populated_shivam_db)

    s02_account = "ACC0020"
    s02_txns = {
        "TXN002130",
        "TXN002138",
        "TXN002146",
        "TXN002152",
        "TXN002155",
        "TXN002160",
        "TXN002172",
    }

    # Verify no alert claims S02's shop account or transactions
    for a in alerts:
        assert s02_account not in a.account_ids, (
            f"Alert {a.alert_id} incorrectly flagged S02 shop account {s02_account}"
        )
        flagged_s02_txns = set(a.txn_ids).intersection(s02_txns)
        assert not flagged_s02_txns, (
            f"Alert {a.alert_id} incorrectly included S02 transactions: {flagged_s02_txns}"
        )


# -----------------------------------------------------------------------------
# 2. Registry & Interface Tests
# -----------------------------------------------------------------------------


def test_registry_registration_and_execution(
    populated_shivam_db: sqlite3.Connection,
) -> None:
    """Verify registry lookups, execution, and case-insensitivity."""
    assert registry.get("RAPID_ONWARD_TRANSFER") is not None
    assert registry.get("rapid_onward_transfer") is not None

    alerts_upper = registry.run_rule("RAPID_ONWARD_TRANSFER", populated_shivam_db)
    alerts_lower = registry.run_rule("rapid_onward_transfer", populated_shivam_db)

    assert len(alerts_upper) == len(alerts_lower)
    assert len(alerts_upper) > 0

    with pytest.raises(ValueError, match="Unknown detection rule"):
        registry.run_rule("NON_EXISTENT_RULE", populated_shivam_db)


def test_custom_registry_instance() -> None:
    """Verify standalone RuleRegistry can register and list custom rules."""
    custom_reg = RuleRegistry()
    assert len(custom_reg.list_rules()) == 0

    rule = RapidOnwardTransferRule()
    custom_reg.register(rule)
    assert len(custom_reg.list_rules()) == 1
    assert custom_reg.get("RAPID_ONWARD_TRANSFER") is rule


# -----------------------------------------------------------------------------
# 3. Boundary & Edge Case Tests
# -----------------------------------------------------------------------------


def test_time_window_boundary(empty_db: sqlite3.Connection) -> None:
    """Verify exact delay boundary: <= max_delay_seconds alerts, > does not."""
    cursor = empty_db.cursor()
    cursor.execute(
        "INSERT INTO accounts (account_id, holder_name, vpa, bank, raw_created_at, created_at_utc) "
        "VALUES ('ACC1', 'A', 'a@bank', 'SBI', '2026-09-01', '2026-09-01T00:00:00+00:00'), "
        "       ('ACC2', 'B', 'b@bank', 'SBI', '2026-09-01', '2026-09-01T00:00:00+00:00'), "
        "       ('ACC3', 'C', 'c@bank', 'SBI', '2026-09-01', '2026-09-01T00:00:00+00:00');"
    )

    # Inflow at t=0
    cursor.execute(
        "INSERT INTO transactions (txn_id, sender_account_id, receiver_account_id, "
        "sender_vpa, receiver_vpa, amount_paise, amount_inr, raw_timestamp, timestamp_utc, "
        "txn_type, status, device_id) VALUES "
        "('T1', 'ACC1', 'ACC2', 'a@bank', 'b@bank', 1000000, 10000.0, "
        "'2026-09-01 10:00:00', '2026-09-01T10:00:00+00:00', 'PAY', 'SUCCESS', 'DEV1');"
    )
    # Outflow at t = 1800s (30m) -> Should alert with max_delay_seconds=1800
    cursor.execute(
        "INSERT INTO transactions (txn_id, sender_account_id, receiver_account_id, "
        "sender_vpa, receiver_vpa, amount_paise, amount_inr, raw_timestamp, timestamp_utc, "
        "txn_type, status, device_id) VALUES "
        "('T2', 'ACC2', 'ACC3', 'b@bank', 'c@bank', 950000, 9500.0, "
        "'2026-09-01 10:30:00', '2026-09-01T10:30:00+00:00', 'PAY', 'SUCCESS', 'DEV1');"
    )
    empty_db.commit()
    cursor.close()

    rule = RapidOnwardTransferRule()

    # Exact boundary (1800s) -> Alerts
    alerts_30m = rule.detect(empty_db, config={"max_delay_seconds": 1800})
    assert len(alerts_30m) == 1
    assert alerts_30m[0].txn_ids == ["T1", "T2"]

    # Strict boundary below 1800s (e.g. 1700s) -> Does not alert
    alerts_strict = rule.detect(empty_db, config={"max_delay_seconds": 1700})
    assert len(alerts_strict) == 0


def test_forwarding_ratio_boundary(empty_db: sqlite3.Connection) -> None:
    """Verify ratio boundary: 80% alerts, 79% does not alert."""
    cursor = empty_db.cursor()
    cursor.execute(
        "INSERT INTO accounts (account_id, holder_name, vpa, bank, raw_created_at, created_at_utc) "
        "VALUES ('ACC1', 'A', 'a@bank', 'SBI', '2026-09-01', '2026-09-01T00:00:00+00:00'), "
        "       ('ACC2', 'B', 'b@bank', 'SBI', '2026-09-01', '2026-09-01T00:00:00+00:00'), "
        "       ('ACC3', 'C', 'c@bank', 'SBI', '2026-09-01', '2026-09-01T00:00:00+00:00');"
    )
    # Inflow: Rs 10,000
    cursor.execute(
        "INSERT INTO transactions (txn_id, sender_account_id, receiver_account_id, "
        "sender_vpa, receiver_vpa, amount_paise, amount_inr, raw_timestamp, timestamp_utc, "
        "txn_type, status, device_id) VALUES "
        "('T1', 'ACC1', 'ACC2', 'a@bank', 'b@bank', 1000000, 10000.0, "
        "'2026-09-01 10:00:00', '2026-09-01T10:00:00+00:00', 'PAY', 'SUCCESS', 'DEV1');"
    )
    # Outflow: Rs 7,900 (79% -> below default 80% threshold)
    cursor.execute(
        "INSERT INTO transactions (txn_id, sender_account_id, receiver_account_id, "
        "sender_vpa, receiver_vpa, amount_paise, amount_inr, raw_timestamp, timestamp_utc, "
        "txn_type, status, device_id) VALUES "
        "('T2', 'ACC2', 'ACC3', 'b@bank', 'c@bank', 790000, 7900.0, "
        "'2026-09-01 10:05:00', '2026-09-01T10:05:00+00:00', 'PAY', 'SUCCESS', 'DEV1');"
    )
    empty_db.commit()
    cursor.close()

    rule = RapidOnwardTransferRule()

    # Default 80% minimum ratio -> No alert
    assert len(rule.detect(empty_db)) == 0

    # Configured 75% minimum ratio -> Alerts
    alerts = rule.detect(empty_db, config={"min_forwarding_ratio": 0.75})
    assert len(alerts) == 1
    assert alerts[0].evidence["overall_forwarding_percentage"] == 79.0


def test_failed_transactions_do_not_alert(empty_db: sqlite3.Connection) -> None:
    """Verify transactions with status != SUCCESS are strictly excluded."""
    cursor = empty_db.cursor()
    cursor.execute(
        "INSERT INTO accounts (account_id, holder_name, vpa, bank, raw_created_at, created_at_utc) "
        "VALUES ('ACC1', 'A', 'a@bank', 'SBI', '2026-09-01', '2026-09-01T00:00:00+00:00'), "
        "       ('ACC2', 'B', 'b@bank', 'SBI', '2026-09-01', '2026-09-01T00:00:00+00:00'), "
        "       ('ACC3', 'C', 'c@bank', 'SBI', '2026-09-01', '2026-09-01T00:00:00+00:00');"
    )
    cursor.execute(
        "INSERT INTO transactions (txn_id, sender_account_id, receiver_account_id, "
        "sender_vpa, receiver_vpa, amount_paise, amount_inr, raw_timestamp, timestamp_utc, "
        "txn_type, status, device_id) VALUES "
        "('T1', 'ACC1', 'ACC2', 'a@bank', 'b@bank', 1000000, 10000.0, "
        "'2026-09-01 10:00:00', '2026-09-01T10:00:00+00:00', 'PAY', 'SUCCESS', 'DEV1');"
    )
    # Outflow FAILED
    cursor.execute(
        "INSERT INTO transactions (txn_id, sender_account_id, receiver_account_id, "
        "sender_vpa, receiver_vpa, amount_paise, amount_inr, raw_timestamp, timestamp_utc, "
        "txn_type, status, device_id) VALUES "
        "('T2', 'ACC2', 'ACC3', 'b@bank', 'c@bank', 950000, 9500.0, "
        "'2026-09-01 10:05:00', '2026-09-01T10:05:00+00:00', 'PAY', 'FAILED', 'DEV1');"
    )
    empty_db.commit()
    cursor.close()

    rule = RapidOnwardTransferRule()
    assert len(rule.detect(empty_db)) == 0


def test_direct_refund_is_not_mule_forwarding(empty_db: sqlite3.Connection) -> None:
    """Verify reciprocal refund (B sending back to A) is excluded from mule chains."""
    cursor = empty_db.cursor()
    cursor.execute(
        "INSERT INTO accounts (account_id, holder_name, vpa, bank, raw_created_at, created_at_utc) "
        "VALUES ('ACC1', 'A', 'a@bank', 'SBI', '2026-09-01', '2026-09-01T00:00:00+00:00'), "
        "       ('ACC2', 'B', 'b@bank', 'SBI', '2026-09-01', '2026-09-01T00:00:00+00:00');"
    )
    # ACC1 -> ACC2
    cursor.execute(
        "INSERT INTO transactions (txn_id, sender_account_id, receiver_account_id, "
        "sender_vpa, receiver_vpa, amount_paise, amount_inr, raw_timestamp, timestamp_utc, "
        "txn_type, status, device_id) VALUES "
        "('T1', 'ACC1', 'ACC2', 'a@bank', 'b@bank', 1000000, 10000.0, "
        "'2026-09-01 10:00:00', '2026-09-01T10:00:00+00:00', 'PAY', 'SUCCESS', 'DEV1');"
    )
    # ACC2 -> ACC1 (Immediate refund)
    cursor.execute(
        "INSERT INTO transactions (txn_id, sender_account_id, receiver_account_id, "
        "sender_vpa, receiver_vpa, amount_paise, amount_inr, raw_timestamp, timestamp_utc, "
        "txn_type, status, device_id) VALUES "
        "('T2', 'ACC2', 'ACC1', 'b@bank', 'a@bank', 1000000, 10000.0, "
        "'2026-09-01 10:02:00', '2026-09-01T10:02:00+00:00', 'PAY', 'SUCCESS', 'DEV1');"
    )
    empty_db.commit()
    cursor.close()

    rule = RapidOnwardTransferRule()
    assert len(rule.detect(empty_db)) == 0


def test_idempotent_execution_produces_identical_alerts(
    empty_db: sqlite3.Connection,
) -> None:
    """Verify repeated execution returns identical alerts and deterministic IDs."""
    cursor = empty_db.cursor()
    cursor.execute(
        "INSERT INTO accounts (account_id, holder_name, vpa, bank, raw_created_at, created_at_utc) "
        "VALUES ('ACC1', 'A', 'a@bank', 'SBI', '2026-09-01', '2026-09-01T00:00:00+00:00'), "
        "       ('ACC2', 'B', 'b@bank', 'SBI', '2026-09-01', '2026-09-01T00:00:00+00:00'), "
        "       ('ACC3', 'C', 'c@bank', 'SBI', '2026-09-01', '2026-09-01T00:00:00+00:00');"
    )
    cursor.execute(
        "INSERT INTO transactions (txn_id, sender_account_id, receiver_account_id, "
        "sender_vpa, receiver_vpa, amount_paise, amount_inr, raw_timestamp, timestamp_utc, "
        "txn_type, status, device_id) VALUES "
        "('T1', 'ACC1', 'ACC2', 'a@bank', 'b@bank', 1000000, 10000.0, "
        "'2026-09-01 10:00:00', '2026-09-01T10:00:00+00:00', 'PAY', 'SUCCESS', 'DEV1'), "
        "('T2', 'ACC2', 'ACC3', 'b@bank', 'c@bank', 950000, 9500.0, "
        "'2026-09-01 10:05:00', '2026-09-01T10:05:00+00:00', 'PAY', 'SUCCESS', 'DEV1');"
    )
    empty_db.commit()
    cursor.close()

    rule = RapidOnwardTransferRule()
    run1 = rule.detect(empty_db)
    run2 = rule.detect(empty_db)

    assert len(run1) == len(run2) == 1
    assert run1[0].alert_id == run2[0].alert_id
    assert run1[0].score == run2[0].score
    assert run1[0].evidence == run2[0].evidence
