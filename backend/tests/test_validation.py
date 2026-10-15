"""Unit tests for dataset inspection, validation framework, and Aryan alert bundle contract."""

import csv
import json
from datetime import timezone
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from app.validation.dataset_validator import (
    validate_alert_bundle,
    validate_expected_results,
    validate_source_dataset,
)
from app.validation.models import (
    AlertBundle,
    parse_inr_amount,
    parse_ist_timestamp,
    parse_utc_timestamp,
)

IST = ZoneInfo("Asia/Kolkata")


# --- 1. Timestamp & Timezone Tests ---


def test_ist_naive_timestamp_conversion_to_utc():
    """Verify naive timestamp is interpreted as IST (Asia/Kolkata) and converted to UTC."""
    naive_str = "2026-09-03 00:18:50"
    utc_dt, raw = parse_ist_timestamp(naive_str)

    assert raw == naive_str
    assert utc_dt.tzinfo == timezone.utc
    # 00:18:50 in IST (UTC+5:30) is 18:48:50 on previous day in UTC
    assert utc_dt.year == 2026
    assert utc_dt.month == 9
    assert utc_dt.day == 2
    assert utc_dt.hour == 18
    assert utc_dt.minute == 48
    assert utc_dt.second == 50


def test_utc_z_timestamp_is_not_treated_as_ist():
    """Verify UTC timestamp with Z suffix is parsed as UTC without IST offset shift."""
    utc_str = "2026-10-15T12:00:00Z"
    utc_dt, raw = parse_ist_timestamp(utc_str)

    assert utc_dt.tzinfo == timezone.utc
    assert utc_dt.year == 2026
    assert utc_dt.month == 10
    assert utc_dt.day == 15
    assert utc_dt.hour == 12
    assert utc_dt.minute == 0
    assert utc_dt.second == 0


def test_parse_utc_timestamp_requires_timezone():
    """Verify parse_utc_timestamp rejects naive timestamps."""
    with pytest.raises(ValueError, match="must be explicitly timezone-aware"):
        parse_utc_timestamp("2026-10-15 12:00:00")

    aware = parse_utc_timestamp("2026-10-15T12:00:00Z")
    assert aware.tzinfo == timezone.utc
    assert aware.hour == 12


def test_invalid_timestamp_format_raises_value_error():
    """Verify malformed timestamp strings fail safely."""
    with pytest.raises(ValueError, match="Invalid timestamp format"):
        parse_ist_timestamp("not-a-valid-date-time")


# --- 2. Amount and Currency (INR) Tests ---


def test_inr_amount_valid_decimal_and_paise():
    """Verify decimal-safe amount parsing and paise integer conversion."""
    dec, paise = parse_inr_amount("1234.50")
    assert dec == Decimal("1234.50")
    assert paise == 123450

    dec2, paise2 = parse_inr_amount(45.5)
    assert dec2 == Decimal("45.5")
    assert paise2 == 4550


def test_inr_amount_rejects_more_than_two_decimal_places():
    """Verify amounts with more than two decimal places are rejected."""
    with pytest.raises(ValueError, match="more than two decimal places"):
        parse_inr_amount("100.555")


def test_inr_amount_rejects_negative_or_zero():
    """Verify negative or zero amounts are rejected."""
    with pytest.raises(ValueError, match="Amount must be positive"):
        parse_inr_amount("-50.00")
    with pytest.raises(ValueError, match="Amount must be positive"):
        parse_inr_amount("0.00")


def test_inr_amount_rejects_invalid_numeric():
    """Verify non-numeric amount strings fail safely."""
    with pytest.raises(ValueError, match="Invalid numeric amount"):
        parse_inr_amount("abc")


# --- 3. Dataset Validator Tests with Fixtures ---


@pytest.fixture
def valid_dataset_dir(tmp_path: Path) -> Path:
    """Create a minimal valid synthetic dataset."""
    # accounts.csv
    accounts_csv = tmp_path / "accounts.csv"
    with open(accounts_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["account_id", "holder_name", "vpa", "bank", "created_at"])
        writer.writerow(["ACC0001", "Alice Doe", "alice@synaxis", "AXIS", "2024-01-01"])
        writer.writerow(["ACC0002", "Bob Smith", "bob@synsbi", "SBI", "2024-01-02"])

    # devices.csv
    devices_csv = tmp_path / "devices.csv"
    with open(devices_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["device_id", "account_id"])
        writer.writerow(["DEV0001", "ACC0001"])
        writer.writerow(["DEV0001", "ACC0002"])  # shared device

    # transactions.csv
    txns_csv = tmp_path / "transactions.csv"
    with open(txns_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "txn_id",
                "timestamp",
                "sender_vpa",
                "receiver_vpa",
                "amount",
                "txn_type",
                "status",
                "device_id",
            ]
        )
        writer.writerow(
            [
                "TXN000001",
                "2026-09-10 14:30:00",
                "alice@synaxis",
                "bob@synsbi",
                "500.00",
                "PAY",
                "SUCCESS",
                "DEV0001",
            ]
        )

    # complaints.csv
    complaints_csv = tmp_path / "complaints.csv"
    with open(complaints_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["complaint_id", "victim_vpa", "txn_id", "complaint_date"])
        writer.writerow(["CMP0001", "alice@synaxis", "TXN000001", "2026-09-11"])

    return tmp_path


def test_validate_valid_dataset_passes(valid_dataset_dir: Path):
    """Verify minimal valid dataset passes with correct entity counts."""
    res = validate_source_dataset(valid_dataset_dir)
    assert res.is_valid is True
    assert res.account_count == 2
    assert res.device_count == 2
    assert res.unique_devices == 1
    assert res.shared_devices == 1
    assert res.transaction_count == 1
    assert res.complaint_count == 1
    assert len(res.errors) == 0


def test_merchants_absence_is_not_an_error(valid_dataset_dir: Path):
    """Verify merchant data absence does not fail validation."""
    assert not (valid_dataset_dir / "merchants.csv").exists()
    res = validate_source_dataset(valid_dataset_dir)
    assert res.is_valid is True


def test_missing_required_file_fails(tmp_path: Path):
    """Verify validation fails when a required CSV is missing."""
    # Only create accounts.csv
    with open(tmp_path / "accounts.csv", "w", newline="", encoding="utf-8") as f:
        f.write("account_id,holder_name,vpa,bank,created_at\n")
    res = validate_source_dataset(tmp_path)
    assert res.is_valid is False
    assert any("Missing required source dataset file" in err for err in res.errors)


def test_duplicate_primary_id_detected(valid_dataset_dir: Path):
    """Verify duplicate account_id fails validation."""
    with open(valid_dataset_dir / "accounts.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ACC0001", "Duplicate Alice", "dup@synaxis", "AXIS", "2024-01-01"])

    res = validate_source_dataset(valid_dataset_dir)
    assert res.is_valid is False
    assert any("Duplicate account_id 'ACC0001'" in err for err in res.errors)


def test_broken_foreign_key_in_transactions(valid_dataset_dir: Path):
    """Verify unknown sender_vpa or device_id fails referential check."""
    with open(valid_dataset_dir / "transactions.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "TXN000002",
                "2026-09-10 15:00:00",
                "unknown@synaxis",
                "bob@synsbi",
                "100.00",
                "PAY",
                "SUCCESS",
                "DEV9999",
            ]
        )

    res = validate_source_dataset(valid_dataset_dir)
    assert res.is_valid is False
    assert any("Unknown sender_vpa 'unknown@synaxis'" in err for err in res.errors)
    assert any("Unknown device_id 'DEV9999'" in err for err in res.errors)


def test_broken_complaint_foreign_key(valid_dataset_dir: Path):
    """Verify unknown txn_id in complaints fails referential check."""
    with open(valid_dataset_dir / "complaints.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["CMP0002", "alice@synaxis", "TXN999999", "2026-09-12"])

    res = validate_source_dataset(valid_dataset_dir)
    assert res.is_valid is False
    assert any(
        "Complaint txn_id 'TXN999999' not found in transactions.csv" in err for err in res.errors
    )


# --- 4. Aryan Alert Bundle Contract Tests ---


@pytest.fixture
def valid_alert_bundle_dict() -> dict:
    return {
        "dataset_id": "anvik_v1",
        "generated_at": "2026-10-15T12:00:00Z",
        "amount_unit": "INR",
        "count": 2,
        "alerts": [
            {
                "alert_id": "ALT0001",
                "rule_id": "rapid_onward_transfer",
                "title": "Rapid Chain Movement",
                "priority": "HIGH",
                "score": 92.5,
                "created_at": "2026-10-15T12:05:00Z",
                "account_ids": ["ACC0011", "ACC0012"],
                "vpas": ["a@syn", "b@syn"],
                "txn_ids": ["TXN001945"],
                "evidence": {"hop_count": 3, "retention_pct": 0.05},
                "explanation": "Funds transferred onward within 5 minutes.",
                "limitations": [],
                "alternative_explanations": ["High-frequency merchant"],
                "complaint_ids": [],
                "related_alert_ids": ["ALT0002"],
                "ring_id": "RNG0001",
            },
            {
                "alert_id": "ALT0002",
                "rule_id": "transaction_cycle",
                "title": "Circular Transaction Loop",
                "priority": "HIGH",
                "score": 88.0,
                "created_at": "2026-10-15T12:06:00Z",
                "account_ids": ["ACC0012", "ACC0013"],
                "vpas": ["b@syn", "c@syn"],
                "txn_ids": ["TXN001946"],
                "evidence": {"loop_length": 3},
                "explanation": "Circular funds flow detected.",
                "limitations": [],
                "alternative_explanations": [],
                "complaint_ids": [],
                "related_alert_ids": ["ALT0001"],
                "ring_id": "RNG0001",
            },
        ],
        "rings": [
            {
                "ring_id": "RNG0001",
                "alert_ids": ["ALT0001", "ALT0002"],
                "account_ids": ["ACC0011", "ACC0012", "ACC0013"],
                "pattern_type": "MULE_CHAIN",
            }
        ],
        "account_summaries": [
            {
                "account_id": "ACC0011",
                "vpa": "a@syn",
                "role": "SOURCE",
                "total_sent_inr": 48000.0,
                "total_received_inr": 0.0,
            }
        ],
    }


def test_valid_alert_bundle_model_validation(valid_alert_bundle_dict):
    """Verify valid alert bundle dictionary conforms to AlertBundle schema."""
    bundle = AlertBundle.model_validate(valid_alert_bundle_dict)
    assert bundle.count == 2
    assert len(bundle.alerts) == 2
    assert bundle.dataset_id == "anvik_v1"
    assert bundle.generated_at.tzinfo == timezone.utc


def test_alert_bundle_rejects_count_mismatch(valid_alert_bundle_dict):
    """Verify alert bundle fails validation when count does not match alerts length."""
    valid_alert_bundle_dict["count"] = 5  # mismatch
    with pytest.raises(ValueError, match="does not match alerts length"):
        AlertBundle.model_validate(valid_alert_bundle_dict)


def test_alert_bundle_rejects_duplicate_alert_ids(valid_alert_bundle_dict):
    """Verify alert bundle fails when alert_id is duplicated."""
    valid_alert_bundle_dict["alerts"][1]["alert_id"] = "ALT0001"
    with pytest.raises(ValueError, match="Duplicate alert_id"):
        AlertBundle.model_validate(valid_alert_bundle_dict)


def test_alert_bundle_rejects_unknown_ring_reference(valid_alert_bundle_dict):
    """Verify alert bundle fails when an alert references a non-existent ring_id."""
    valid_alert_bundle_dict["alerts"][0]["ring_id"] = "UNKNOWN_RING"
    with pytest.raises(ValueError, match="references unknown ring_id"):
        AlertBundle.model_validate(valid_alert_bundle_dict)


def test_validate_alert_bundle_file(tmp_path: Path, valid_alert_bundle_dict):
    """Verify validate_alert_bundle function on JSON file."""
    bundle_file = tmp_path / "bundle.json"
    with open(bundle_file, "w", encoding="utf-8") as f:
        json.dump(valid_alert_bundle_dict, f)

    res = validate_alert_bundle(bundle_file)
    assert res.is_valid is True
    assert res.alert_count == 2
    assert res.ring_count == 1


# --- 5. Real Shivam Dataset Verification ---


def test_real_incoming_shivam_dataset_passes_audit():
    """Verify actual Shivam dataset in backend/data/incoming passes 100% cleanly."""
    incoming_dir = Path("backend/data/incoming")
    if not incoming_dir.exists():
        pytest.skip("backend/data/incoming not present in current working environment")

    res = validate_source_dataset(incoming_dir)
    assert res.is_valid is True
    assert res.account_count == 200
    assert res.device_count == 233
    assert res.complaint_count == 10
    assert res.transaction_count == 3129
    assert len(res.errors) == 0

    # Verify expected_results.json
    exp_file = incoming_dir / "expected_results.json"
    assert exp_file.exists()
    exp_res = validate_expected_results(exp_file, dataset_summary=res)
    assert exp_res.is_valid is True
    assert exp_res.scenario_count == 10
    assert exp_res.alert_scenario_count == 5
    assert exp_res.control_scenario_count == 5
    assert len(exp_res.errors) == 0
