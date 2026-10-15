"""Dataset and alert bundle validation engine."""

import csv
import json
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

from app.validation.models import (
    AlertBundle,
    ExpectedScenario,
    parse_inr_amount,
    parse_ist_timestamp,
)


@dataclass
class DatasetValidationResult:
    """Detailed result of source dataset validation."""

    is_valid: bool
    data_dir: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    # Entity counts
    account_count: int = 0
    device_count: int = 0
    complaint_count: int = 0
    transaction_count: int = 0

    # Inferred details
    unique_devices: int = 0
    shared_devices: int = 0
    min_amount_inr: Optional[Decimal] = None
    max_amount_inr: Optional[Decimal] = None
    min_timestamp_ist: Optional[str] = None
    max_timestamp_ist: Optional[str] = None
    min_timestamp_utc: Optional[str] = None
    max_timestamp_utc: Optional[str] = None

    banks_found: dict[str, int] = field(default_factory=dict)
    txn_types: dict[str, int] = field(default_factory=dict)
    txn_statuses: dict[str, int] = field(default_factory=dict)

    # Identifiers for cross-referencing
    known_account_ids: set[str] = field(default_factory=set)
    known_vpas: set[str] = field(default_factory=set)
    known_device_ids: set[str] = field(default_factory=set)
    known_txn_ids: set[str] = field(default_factory=set)
    known_complaint_ids: set[str] = field(default_factory=set)


@dataclass
class ScenarioValidationResult:
    """Detailed result of scenario test reference validation."""

    is_valid: bool
    file_path: str
    scenario_count: int = 0
    alert_scenario_count: int = 0
    control_scenario_count: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    scenarios: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class AlertBundleValidationResult:
    """Detailed result of Aryan's alert bundle contract validation."""

    is_valid: bool
    file_path: str
    dataset_id: Optional[str] = None
    alert_count: int = 0
    ring_count: int = 0
    account_summary_count: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_source_dataset(data_dir: Path) -> DatasetValidationResult:
    """Validate all files in Shivam's raw source dataset directory.

    Note: Merchant files/fields are intentionally optional and absent.
    """
    result = DatasetValidationResult(is_valid=True, data_dir=str(data_dir))

    if not data_dir.exists() or not data_dir.is_dir():
        result.is_valid = False
        result.errors.append(
            f"Source data directory does not exist or is not a directory: {data_dir}"
        )
        return result

    # Required files
    accounts_file = data_dir / "accounts.csv"
    devices_file = data_dir / "devices.csv"
    complaints_file = data_dir / "complaints.csv"
    txns_file = data_dir / "transactions.csv"

    # Optional merchant file check (for reporting only)
    merchants_file = data_dir / "merchants.csv"
    if merchants_file.exists():
        result.warnings.append(
            "Found unexpected merchants.csv; merchant data was planned absent."
        )

    for req_file, name in [
        (accounts_file, "accounts.csv"),
        (devices_file, "devices.csv"),
        (complaints_file, "complaints.csv"),
        (txns_file, "transactions.csv"),
    ]:
        if not req_file.exists():
            result.is_valid = False
            result.errors.append(f"Missing required source dataset file: {name}")

    if not result.is_valid:
        return result

    # 1. Validate accounts.csv
    seen_account_ids: set[str] = set()
    seen_vpas: set[str] = set()
    try:
        with open(accounts_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            expected_headers = {"account_id", "holder_name", "vpa", "bank", "created_at"}
            if not reader.fieldnames or not expected_headers.issubset(set(reader.fieldnames)):
                result.errors.append(
                    f"accounts.csv header mismatch. Expected {expected_headers}"
                )
                result.is_valid = False
                return result

            for row_idx, row in enumerate(reader, start=2):
                acc_id = row.get("account_id", "").strip()
                vpa = row.get("vpa", "").strip()
                bank = row.get("bank", "").strip()
                name = row.get("holder_name", "").strip()

                if not acc_id or not vpa or not bank or not name:
                    result.errors.append(f"accounts.csv row {row_idx}: Missing required fields.")
                    result.is_valid = False
                    continue

                if acc_id in seen_account_ids:
                    result.errors.append(
                        f"accounts.csv row {row_idx}: Duplicate account_id '{acc_id}'"
                    )
                    result.is_valid = False
                seen_account_ids.add(acc_id)

                if vpa in seen_vpas:
                    result.errors.append(f"accounts.csv row {row_idx}: Duplicate vpa '{vpa}'")
                    result.is_valid = False
                seen_vpas.add(vpa)

                result.banks_found[bank] = result.banks_found.get(bank, 0) + 1

        result.account_count = len(seen_account_ids)
        result.known_account_ids = seen_account_ids
        result.known_vpas = seen_vpas
    except Exception as e:
        result.errors.append(f"Failed to read accounts.csv: {e}")
        result.is_valid = False

    # 2. Validate devices.csv
    device_to_accounts: dict[str, set[str]] = {}
    try:
        with open(devices_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            expected_headers = {"device_id", "account_id"}
            if not reader.fieldnames or not expected_headers.issubset(set(reader.fieldnames)):
                result.errors.append(
                    f"devices.csv header mismatch. Expected {expected_headers}"
                )
                result.is_valid = False
                return result

            dev_row_count = 0
            for row_idx, row in enumerate(reader, start=2):
                dev_id = row.get("device_id", "").strip()
                acc_id = row.get("account_id", "").strip()
                if not dev_id or not acc_id:
                    result.errors.append(
                        f"devices.csv row {row_idx}: Missing device_id or account_id."
                    )
                    result.is_valid = False
                    continue

                dev_row_count += 1
                result.known_device_ids.add(dev_id)
                device_to_accounts.setdefault(dev_id, set()).add(acc_id)

                # Referential check: account must exist
                if acc_id not in result.known_account_ids:
                    result.errors.append(
                        f"devices.csv row {row_idx}: References unknown account_id '{acc_id}'"
                    )
                    result.is_valid = False

        result.device_count = dev_row_count
        result.unique_devices = len(device_to_accounts)
        result.shared_devices = sum(1 for accs in device_to_accounts.values() if len(accs) > 1)
    except Exception as e:
        result.errors.append(f"Failed to read devices.csv: {e}")
        result.is_valid = False

    # 3. Validate complaints.csv
    seen_complaint_ids: set[str] = set()
    complaint_rows: list[dict[str, str]] = []
    try:
        with open(complaints_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            expected_headers = {"complaint_id", "victim_vpa", "txn_id", "complaint_date"}
            if not reader.fieldnames or not expected_headers.issubset(set(reader.fieldnames)):
                result.errors.append(
                    f"complaints.csv header mismatch. Expected {expected_headers}"
                )
                result.is_valid = False
                return result

            for row_idx, row in enumerate(reader, start=2):
                cmp_id = row.get("complaint_id", "").strip()
                vic_vpa = row.get("victim_vpa", "").strip()
                txn_id = row.get("txn_id", "").strip()

                if not cmp_id or not vic_vpa or not txn_id:
                    result.errors.append(f"complaints.csv row {row_idx}: Missing required fields.")
                    result.is_valid = False
                    continue

                if cmp_id in seen_complaint_ids:
                    result.errors.append(
                        f"complaints.csv row {row_idx}: Duplicate complaint_id '{cmp_id}'"
                    )
                    result.is_valid = False
                seen_complaint_ids.add(cmp_id)

                # Referential check: victim_vpa must exist
                if vic_vpa not in result.known_vpas:
                    result.errors.append(
                        f"complaints.csv row {row_idx}: Unknown victim_vpa '{vic_vpa}'"
                    )
                    result.is_valid = False

                complaint_rows.append(row)

        result.complaint_count = len(seen_complaint_ids)
        result.known_complaint_ids = seen_complaint_ids
    except Exception as e:
        result.errors.append(f"Failed to read complaints.csv: {e}")
        result.is_valid = False

    # 4. Validate transactions.csv
    seen_txn_ids: set[str] = set()
    min_amt: Optional[Decimal] = None
    max_amt: Optional[Decimal] = None
    min_ts_ist: Optional[str] = None
    max_ts_ist: Optional[str] = None
    min_ts_utc: Optional[str] = None
    max_ts_utc: Optional[str] = None

    try:
        with open(txns_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            expected_headers = {
                "txn_id",
                "timestamp",
                "sender_vpa",
                "receiver_vpa",
                "amount",
                "txn_type",
                "status",
                "device_id",
            }
            if not reader.fieldnames or not expected_headers.issubset(set(reader.fieldnames)):
                result.errors.append(
                    f"transactions.csv header mismatch. Expected {expected_headers}"
                )
                result.is_valid = False
                return result

            for row_idx, row in enumerate(reader, start=2):
                txn_id = row.get("txn_id", "").strip()
                ts_raw = row.get("timestamp", "").strip()
                sender = row.get("sender_vpa", "").strip()
                receiver = row.get("receiver_vpa", "").strip()
                amt_raw = row.get("amount", "").strip()
                txn_type = row.get("txn_type", "").strip()
                status = row.get("status", "").strip()
                dev_id = row.get("device_id", "").strip()

                if not txn_id or not ts_raw or not sender or not receiver or not amt_raw:
                    result.errors.append(
                        f"transactions.csv row {row_idx}: Missing required fields."
                    )
                    result.is_valid = False
                    continue

                if txn_id in seen_txn_ids:
                    result.errors.append(
                        f"transactions.csv row {row_idx}: Duplicate txn_id '{txn_id}'"
                    )
                    result.is_valid = False
                seen_txn_ids.add(txn_id)

                # Check referential integrity
                if sender not in result.known_vpas:
                    result.errors.append(
                        f"transactions.csv row {row_idx}: Unknown sender_vpa '{sender}'"
                    )
                    result.is_valid = False

                if receiver not in result.known_vpas:
                    result.errors.append(
                        f"transactions.csv row {row_idx}: Unknown receiver_vpa '{receiver}'"
                    )
                    result.is_valid = False

                if dev_id and dev_id not in result.known_device_ids:
                    result.errors.append(
                        f"transactions.csv row {row_idx}: Unknown device_id '{dev_id}'"
                    )
                    result.is_valid = False

                # Validate amount (INR decimal-safe)
                try:
                    dec_amt, _ = parse_inr_amount(amt_raw)
                    if min_amt is None or dec_amt < min_amt:
                        min_amt = dec_amt
                    if max_amt is None or dec_amt > max_amt:
                        max_amt = dec_amt
                except ValueError as e:
                    result.errors.append(f"transactions.csv row {row_idx}: {e}")
                    result.is_valid = False

                # Validate timestamp (IST naive -> UTC conversion)
                try:
                    utc_dt, _ = parse_ist_timestamp(ts_raw)
                    utc_iso = utc_dt.isoformat()
                    if min_ts_ist is None or ts_raw < min_ts_ist:
                        min_ts_ist = ts_raw
                    if max_ts_ist is None or ts_raw > max_ts_ist:
                        max_ts_ist = ts_raw
                    if min_ts_utc is None or utc_iso < min_ts_utc:
                        min_ts_utc = utc_iso
                    if max_ts_utc is None or utc_iso > max_ts_utc:
                        max_ts_utc = utc_iso
                except ValueError as e:
                    result.errors.append(f"transactions.csv row {row_idx}: {e}")
                    result.is_valid = False

                result.txn_types[txn_type] = result.txn_types.get(txn_type, 0) + 1
                result.txn_statuses[status] = result.txn_statuses.get(status, 0) + 1

        result.transaction_count = len(seen_txn_ids)
        result.known_txn_ids = seen_txn_ids
        result.min_amount_inr = min_amt
        result.max_amount_inr = max_amt
        result.min_timestamp_ist = min_ts_ist
        result.max_timestamp_ist = max_ts_ist
        result.min_timestamp_utc = min_ts_utc
        result.max_timestamp_utc = max_ts_utc

    except Exception as e:
        result.errors.append(f"Failed to read transactions.csv: {e}")
        result.is_valid = False

    # Check complaints txn_id reference against actual transactions.csv
    for r in complaint_rows:
        t_id = r.get("txn_id", "")
        if t_id not in result.known_txn_ids:
            result.errors.append(
                f"complaints.csv: Complaint txn_id '{t_id}' not found in transactions.csv"
            )
            result.is_valid = False

    if result.errors:
        result.is_valid = False

    return result


def validate_expected_results(
    expected_path: Path,
    dataset_summary: Optional[DatasetValidationResult] = None,
) -> ScenarioValidationResult:
    """Validate the 10-scenario ground-truth expected_results.json."""
    res = ScenarioValidationResult(is_valid=True, file_path=str(expected_path))

    if not expected_path.exists():
        res.is_valid = False
        res.errors.append(f"Expected results file not found: {expected_path}")
        return res

    try:
        with open(expected_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        res.is_valid = False
        res.errors.append(f"Failed to parse expected_results.json: {e}")
        return res

    if not isinstance(data, list):
        res.is_valid = False
        res.errors.append("expected_results.json root must be a list of scenario objects")
        return res

    seen_sids: set[str] = set()
    for idx, item in enumerate(data):
        try:
            scenario = ExpectedScenario.model_validate(item)
            sid = scenario.scenario_id
            if sid in seen_sids:
                res.errors.append(f"Duplicate scenario_id '{sid}' at index {idx}")
                res.is_valid = False
            seen_sids.add(sid)

            if scenario.should_alert:
                res.alert_scenario_count += 1
            else:
                res.control_scenario_count += 1

            # Cross-reference with source dataset if provided
            if dataset_summary:
                for acc in scenario.accounts:
                    if acc not in dataset_summary.known_account_ids:
                        res.errors.append(f"Scenario '{sid}' references unknown account_id '{acc}'")
                        res.is_valid = False

                for tid in scenario.txn_ids:
                    if tid not in dataset_summary.known_txn_ids:
                        res.errors.append(f"Scenario '{sid}' references unknown txn_id '{tid}'")
                        res.is_valid = False

                for cid in scenario.complaint_ids:
                    if cid not in dataset_summary.known_complaint_ids:
                        res.errors.append(
                            f"Scenario '{sid}' references unknown complaint_id '{cid}'"
                        )
                        res.is_valid = False

                for dev in scenario.devices:
                    if dev not in dataset_summary.known_device_ids:
                        res.errors.append(f"Scenario '{sid}' references unknown device_id '{dev}'")
                        res.is_valid = False

            res.scenarios.append(
                {
                    "scenario_id": sid,
                    "should_alert": scenario.should_alert,
                    "rules": scenario.expected_rules,
                    "accounts_count": len(scenario.accounts),
                    "txns_count": len(scenario.txn_ids),
                }
            )
        except Exception as e:
            res.errors.append(f"Scenario at index {idx} failed validation: {e}")
            res.is_valid = False

    res.scenario_count = len(seen_sids)
    if res.errors:
        res.is_valid = False

    return res


def validate_alert_bundle(
    bundle_path: Path,
    dataset_summary: Optional[DatasetValidationResult] = None,
) -> AlertBundleValidationResult:
    """Validate Aryan's alert bundle contract independently or cross-referenced with dataset."""
    res = AlertBundleValidationResult(is_valid=True, file_path=str(bundle_path))

    if not bundle_path.exists():
        res.is_valid = False
        res.errors.append(f"Alert bundle file not found: {bundle_path}")
        return res

    try:
        with open(bundle_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        res.is_valid = False
        res.errors.append(f"Failed to parse alert bundle JSON: {e}")
        return res

    try:
        bundle = AlertBundle.model_validate(data)
        res.dataset_id = bundle.dataset_id
        res.alert_count = len(bundle.alerts)
        res.ring_count = len(bundle.rings)
        res.account_summary_count = len(bundle.account_summaries)

        # Cross reference with dataset if provided
        if dataset_summary:
            for alert in bundle.alerts:
                for acc in alert.account_ids:
                    if acc not in dataset_summary.known_account_ids:
                        res.warnings.append(
                            f"Alert '{alert.alert_id}' references unknown account '{acc}'"
                        )
                for vpa in alert.vpas:
                    if vpa not in dataset_summary.known_vpas:
                        res.warnings.append(
                            f"Alert '{alert.alert_id}' references unknown vpa '{vpa}'"
                        )
                for tid in alert.txn_ids:
                    if tid not in dataset_summary.known_txn_ids:
                        res.warnings.append(
                            f"Alert '{alert.alert_id}' references unknown txn '{tid}'"
                        )
                for cid in alert.complaint_ids:
                    if cid not in dataset_summary.known_complaint_ids:
                        res.warnings.append(
                            f"Alert '{alert.alert_id}' references unknown complaint '{cid}'"
                        )
    except Exception as e:
        res.errors.append(f"Alert bundle validation failed: {e}")
        res.is_valid = False

    return res
