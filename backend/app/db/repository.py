"""Database repository functions for Anvik source entities."""

from typing import Any, Optional


def get_accounts(conn: Any) -> list[dict[str, Any]]:
    """Fetch all accounts from database."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT account_id, holder_name, vpa, bank, raw_created_at, created_at_utc "
        "FROM accounts ORDER BY account_id;"
    )
    rows = cursor.fetchall()
    cursor.close()
    return [
        {
            "account_id": r[0],
            "holder_name": r[1],
            "vpa": r[2],
            "bank": r[3],
            "raw_created_at": r[4],
            "created_at_utc": r[5],
        }
        for r in rows
    ]


def get_devices(conn: Any) -> list[dict[str, Any]]:
    """Fetch all unique devices from database."""
    cursor = conn.cursor()
    cursor.execute("SELECT device_id FROM devices ORDER BY device_id;")
    rows = cursor.fetchall()
    cursor.close()
    return [{"device_id": r[0]} for r in rows]


def get_account_devices(conn: Any) -> list[dict[str, Any]]:
    """Fetch all account-to-device relationships."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT account_id, device_id FROM account_devices ORDER BY account_id, device_id;"
    )
    rows = cursor.fetchall()
    cursor.close()
    return [{"account_id": r[0], "device_id": r[1]} for r in rows]


def get_transactions(
    conn: Any,
    status: Optional[str] = None,
    limit: Optional[int] = None,
) -> list[dict[str, Any]]:
    """Fetch transactions with optional status filter and limit."""
    query = (
        "SELECT txn_id, sender_account_id, receiver_account_id, sender_vpa, receiver_vpa, "
        "amount_paise, amount_inr, raw_timestamp, timestamp_utc, txn_type, status, device_id "
        "FROM transactions"
    )
    params: list[Any] = []
    if status:
        query += " WHERE status = ?"
        params.append(status.upper())

    query += " ORDER BY timestamp_utc"

    if limit is not None and limit > 0:
        query += " LIMIT ?"
        params.append(limit)

    cursor = conn.cursor()
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    cursor.close()

    return [
        {
            "txn_id": r[0],
            "sender_account_id": r[1],
            "receiver_account_id": r[2],
            "sender_vpa": r[3],
            "receiver_vpa": r[4],
            "amount_paise": r[5],
            "amount_inr": r[6],
            "raw_timestamp": r[7],
            "timestamp_utc": r[8],
            "txn_type": r[9],
            "status": r[10],
            "device_id": r[11],
        }
        for r in rows
    ]


def get_complaints(conn: Any) -> list[dict[str, Any]]:
    """Fetch all complaints."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT complaint_id, victim_account_id, victim_vpa, txn_id, "
        "raw_complaint_date, complaint_date_utc FROM complaints ORDER BY complaint_id;"
    )
    rows = cursor.fetchall()
    cursor.close()
    return [
        {
            "complaint_id": r[0],
            "victim_account_id": r[1],
            "victim_vpa": r[2],
            "txn_id": r[3],
            "raw_complaint_date": r[4],
            "complaint_date_utc": r[5],
        }
        for r in rows
    ]


def get_latest_import(conn: Any) -> Optional[dict[str, Any]]:
    """Fetch metadata of latest successful dataset import."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT import_id, dataset_id, data_hash, imported_at_utc, account_count, "
        "device_count, account_device_count, transaction_count, complaint_count, status "
        "FROM dataset_imports ORDER BY imported_at_utc DESC LIMIT 1;"
    )
    row = cursor.fetchone()
    cursor.close()
    if not row:
        return None
    return {
        "import_id": row[0],
        "dataset_id": row[1],
        "data_hash": row[2],
        "imported_at_utc": row[3],
        "account_count": row[4],
        "device_count": row[5],
        "account_device_count": row[6],
        "transaction_count": row[7],
        "complaint_count": row[8],
        "status": row[9],
    }


def clear_synthetic_tables(conn: Any) -> None:
    """Safely clear only synthetic data tables in reverse dependency order."""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM complaints;")
    cursor.execute("DELETE FROM transactions;")
    cursor.execute("DELETE FROM account_devices;")
    cursor.execute("DELETE FROM devices;")
    cursor.execute("DELETE FROM accounts;")
    cursor.close()
    conn.commit()
