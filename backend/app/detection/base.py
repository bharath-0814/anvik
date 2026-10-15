"""Base detection rule abstraction and database query helpers."""

from abc import ABC, abstractmethod
from typing import Any, Optional

from app.detection.models import DetectionAlert


class BaseDetectionRule(ABC):
    """Abstract base class for all explainable Anvik fraud detection rules."""

    rule_id: str
    title: str
    default_priority: str = "HIGH"

    @abstractmethod
    def detect(
        self,
        conn: Any,
        config: Optional[dict[str, Any]] = None,
    ) -> list[DetectionAlert]:
        """Execute detection against the provided database connection.

        Args:
            conn: Open DB connection (SQLite or Turso serverless).
            config: Optional dictionary of rule parameter overrides.

        Returns:
            list[DetectionAlert]: List of structured, evidence-backed detection alerts.
        """
        ...

    def get_complaints_lookup(
        self,
        conn: Any,
    ) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
        """Fetch complaints indexed by txn_id and victim_account_id.

        Returns:
            tuple[dict[str, list[str]], dict[str, list[str]]]:
                (complaints_by_txn, complaints_by_account)
        """
        cursor = conn.cursor()
        cursor.execute(
            "SELECT complaint_id, victim_account_id, txn_id FROM complaints ORDER BY complaint_id;"
        )
        rows = cursor.fetchall()
        cursor.close()

        by_txn: dict[str, list[str]] = {}
        by_acc: dict[str, list[str]] = {}
        for r in rows:
            c_id = str(r[0])
            victim_acc = str(r[1])
            txn_id = str(r[2]) if r[2] else None

            if txn_id:
                by_txn.setdefault(txn_id, []).append(c_id)
            if victim_acc:
                by_acc.setdefault(victim_acc, []).append(c_id)

        return by_txn, by_acc

    def get_accounts_lookup(self, conn: Any) -> dict[str, dict[str, Any]]:
        """Fetch account metadata lookup table.

        Returns:
            dict[str, dict[str, Any]]: Mapping of account_id -> account details.
        """
        cursor = conn.cursor()
        cursor.execute("SELECT account_id, holder_name, vpa, bank FROM accounts;")
        rows = cursor.fetchall()
        cursor.close()

        return {
            str(r[0]): {
                "account_id": str(r[0]),
                "holder_name": str(r[1]),
                "vpa": str(r[2]),
                "bank": str(r[3]),
            }
            for r in rows
        }
