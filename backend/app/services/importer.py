"""Deterministic, repeatable dataset importer for Anvik."""

import csv
import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.db.migrations import run_migrations
from app.db.repository import clear_synthetic_tables, get_latest_import
from app.db.turso import get_turso_connection
from app.validation.dataset_validator import validate_source_dataset
from app.validation.models import parse_inr_amount, parse_ist_timestamp


@dataclass
class ImportResult:
    """Detailed summary of dataset import outcome."""

    is_success: bool
    is_noop: bool
    dataset_id: str
    data_hash: str
    account_count: int
    device_count: int
    account_device_count: int
    transaction_count: int
    complaint_count: int
    message: str


def compute_dataset_hash(data_dir: Path) -> str:
    """Compute a deterministic SHA-256 hash across the 4 source CSV files."""
    hasher = hashlib.sha256()
    for filename in ["accounts.csv", "devices.csv", "complaints.csv", "transactions.csv"]:
        file_path = data_dir / filename
        if file_path.exists():
            with open(file_path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
    return hasher.hexdigest()


def _batch_insert(
    cursor: Any,
    table: str,
    columns: list[str],
    rows: list[tuple[Any, ...]],
    batch_size: int = 50,
) -> None:
    """Insert rows in multi-value batches to minimize round-trips over serverless HTTP."""
    if not rows:
        return
    col_names = ", ".join(columns)
    single_placeholder = f"({', '.join(['?'] * len(columns))})"

    for i in range(0, len(rows), batch_size):
        chunk = rows[i : i + batch_size]
        placeholders = ", ".join([single_placeholder] * len(chunk))
        sql = f"INSERT INTO {table} ({col_names}) VALUES {placeholders};"
        flat_params = [val for row in chunk for val in row]
        cursor.execute(sql, flat_params)


def import_source_dataset(
    data_dir: Path,
    conn: Any = None,
    replace_existing: bool = False,
    dataset_id: str = "shivam_v1",
) -> ImportResult:
    """Validate and import Shivam's raw source dataset into Turso or SQLite.

    Args:
        data_dir: Path to directory containing accounts.csv, devices.csv, etc.
        conn: Optional DB-API connection (uses get_turso_connection() if None).
        replace_existing: If True, safely replaces currently loaded synthetic tables.
        dataset_id: Identifier for this dataset revision.

    Returns:
        ImportResult: Detailed import metrics and status.
    """
    # 1. Run local validator first
    validation_res = validate_source_dataset(data_dir)
    if not validation_res.is_valid:
        error_summary = "; ".join(validation_res.errors[:5])
        raise ValueError(f"Dataset validation failed: {error_summary}")

    # 2. Compute deterministic content hash
    data_hash = compute_dataset_hash(data_dir)

    should_close = False
    if conn is None:
        conn = get_turso_connection()
        should_close = True

    try:
        # Ensure schema migrations are applied
        run_migrations(conn=conn)

        # 3. Check latest import status for idempotency
        latest = get_latest_import(conn)
        if latest and latest.get("status") == "SUCCESS" and not replace_existing:
            if latest.get("data_hash") == data_hash:
                return ImportResult(
                    is_success=True,
                    is_noop=True,
                    dataset_id=latest["dataset_id"],
                    data_hash=data_hash,
                    account_count=latest["account_count"],
                    device_count=latest["device_count"],
                    account_device_count=latest["account_device_count"],
                    transaction_count=latest["transaction_count"],
                    complaint_count=latest["complaint_count"],
                    message="Dataset already imported with matching data hash (idempotent no-op).",
                )
            else:
                raise ValueError(
                    f"Existing dataset '{latest['dataset_id']}' with different hash is present. "
                    "Use replace_existing=True to overwrite."
                )

        # 4. If replacing, safely clear synthetic tables
        if replace_existing:
            clear_synthetic_tables(conn)

        # 5. Read and insert accounts
        accounts_path = data_dir / "accounts.csv"
        vpa_to_account_id: dict[str, str] = {}
        account_rows: list[tuple[Any, ...]] = []

        with open(accounts_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                acc_id = r["account_id"].strip()
                name = r["holder_name"].strip()
                vpa = r["vpa"].strip()
                bank = r["bank"].strip()
                raw_created = r["created_at"].strip()
                # Preserve date as ISO date
                account_rows.append((acc_id, name, vpa, bank, raw_created, raw_created))
                vpa_to_account_id[vpa] = acc_id

        cursor = conn.cursor()
        _batch_insert(
            cursor,
            "accounts",
            ["account_id", "holder_name", "vpa", "bank", "raw_created_at", "created_at_utc"],
            account_rows,
            batch_size=50,
        )

        # 6. Read and insert devices & account_devices
        devices_path = data_dir / "devices.csv"
        unique_device_ids: set[str] = set()
        account_device_rows: list[tuple[str, str]] = []

        with open(devices_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                dev_id = r["device_id"].strip()
                acc_id = r["account_id"].strip()
                unique_device_ids.add(dev_id)
                account_device_rows.append((acc_id, dev_id))

        _batch_insert(
            cursor,
            "devices",
            ["device_id"],
            [(did,) for did in sorted(unique_device_ids)],
            batch_size=100,
        )

        _batch_insert(
            cursor,
            "account_devices",
            ["account_id", "device_id"],
            account_device_rows,
            batch_size=100,
        )

        # 7. Read and insert transactions
        txns_path = data_dir / "transactions.csv"
        txn_rows: list[tuple[Any, ...]] = []

        with open(txns_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                t_id = r["txn_id"].strip()
                raw_ts = r["timestamp"].strip()
                s_vpa = r["sender_vpa"].strip()
                r_vpa = r["receiver_vpa"].strip()
                amt_str = r["amount"].strip()
                t_type = r["txn_type"].strip()
                st = r["status"].strip()
                d_id = r["device_id"].strip()

                s_acc = vpa_to_account_id[s_vpa]
                r_acc = vpa_to_account_id[r_vpa]

                dec_amt, paise = parse_inr_amount(amt_str)
                utc_dt, _ = parse_ist_timestamp(raw_ts)
                utc_iso = utc_dt.isoformat()

                txn_rows.append(
                    (
                        t_id,
                        s_acc,
                        r_acc,
                        s_vpa,
                        r_vpa,
                        paise,
                        float(dec_amt),
                        raw_ts,
                        utc_iso,
                        t_type,
                        st,
                        d_id,
                    )
                )

        _batch_insert(
            cursor,
            "transactions",
            [
                "txn_id",
                "sender_account_id",
                "receiver_account_id",
                "sender_vpa",
                "receiver_vpa",
                "amount_paise",
                "amount_inr",
                "raw_timestamp",
                "timestamp_utc",
                "txn_type",
                "status",
                "device_id",
            ],
            txn_rows,
            batch_size=50,
        )

        # 8. Read and insert complaints
        complaints_path = data_dir / "complaints.csv"
        complaint_rows: list[tuple[Any, ...]] = []

        with open(complaints_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                c_id = r["complaint_id"].strip()
                vic_vpa = r["victim_vpa"].strip()
                t_id = r["txn_id"].strip()
                raw_c_date = r["complaint_date"].strip()

                vic_acc = vpa_to_account_id[vic_vpa]
                complaint_rows.append((c_id, vic_acc, vic_vpa, t_id, raw_c_date, raw_c_date))

        _batch_insert(
            cursor,
            "complaints",
            [
                "complaint_id",
                "victim_account_id",
                "victim_vpa",
                "txn_id",
                "raw_complaint_date",
                "complaint_date_utc",
            ],
            complaint_rows,
            batch_size=50,
        )

        # 9. Record import metadata
        import_id = f"imp_{uuid.uuid4().hex[:12]}"
        now_utc = datetime.now(timezone.utc).isoformat()
        cursor.execute(
            "INSERT INTO dataset_imports (import_id, dataset_id, data_hash, imported_at_utc, "
            "account_count, device_count, account_device_count, transaction_count, "
            "complaint_count, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
            (
                import_id,
                dataset_id,
                data_hash,
                now_utc,
                len(account_rows),
                len(unique_device_ids),
                len(account_device_rows),
                len(txn_rows),
                len(complaint_rows),
                "SUCCESS",
            ),
        )
        cursor.close()
        conn.commit()

        return ImportResult(
            is_success=True,
            is_noop=False,
            dataset_id=dataset_id,
            data_hash=data_hash,
            account_count=len(account_rows),
            device_count=len(unique_device_ids),
            account_device_count=len(account_device_rows),
            transaction_count=len(txn_rows),
            complaint_count=len(complaint_rows),
            message="Dataset successfully imported into database.",
        )
    finally:
        if should_close and conn is not None:
            conn.close()
