"""Transaction cycle detection rule.

Detects directed circular transaction flows where funds move in a closed loop
across multiple accounts within a defined time window and with high fund retention.
"""

import hashlib
from datetime import datetime, timezone
from typing import Any, Optional

from app.detection.base import BaseDetectionRule
from app.detection.models import DetectionAlert, HopEvidence
from app.detection.scoring import calculate_alert_score


class TransactionCycleRule(BaseDetectionRule):
    """Detection rule for circular fund routing across accounts."""

    rule_id: str = "TRANSACTION_CYCLE"
    title: str = "Circular Transaction Cycle"
    default_priority: str = "HIGH"

    def detect(
        self,
        conn: Any,
        config: Optional[dict[str, Any]] = None,
    ) -> list[DetectionAlert]:
        """Execute detection for transaction cycles.

        Configurable Parameters:
            max_duration_hours (float): Maximum allowed time from first to last
                transaction in cycle (default: 4.0 hours).
            min_cycle_length (int): Minimum distinct accounts in cycle (default: 3).
            max_cycle_length (int): Maximum distinct accounts in cycle (default: 5).
            min_amount_inr (float): Minimum transaction amount in INR (default: 1000.0).
            min_amount_ratio (float): Minimum amount ratio between consecutive hops
                (default: 0.70 / 70%).
            max_amount_ratio (float): Maximum amount ratio between consecutive hops
                (default: 1.25 / 125%).
        """
        cfg = config or {}
        max_duration_sec = float(cfg.get("max_duration_hours", 4.0)) * 3600.0
        min_cycle_len = int(cfg.get("min_cycle_length", 3))
        max_cycle_len = int(cfg.get("max_cycle_length", 5))
        min_amount = float(cfg.get("min_amount_inr", 1000.0))
        min_ratio = float(cfg.get("min_amount_ratio", 0.70))
        max_ratio = float(cfg.get("max_amount_ratio", 1.25))

        complaints_by_txn, complaints_by_acc = self.get_complaints_lookup(conn)
        accounts_map = self.get_accounts_lookup(conn)

        # 1. Fetch all SUCCESS transactions ordered chronologically
        cursor = conn.cursor()
        cursor.execute(
            "SELECT txn_id, sender_account_id, receiver_account_id, sender_vpa, receiver_vpa, "
            "amount_paise, amount_inr, raw_timestamp, timestamp_utc, device_id "
            "FROM transactions "
            "WHERE status = 'SUCCESS' "
            "ORDER BY timestamp_utc ASC;"
        )
        rows = cursor.fetchall()
        cursor.close()

        transactions: list[dict[str, Any]] = []
        for r in rows:
            ts_str = str(r[8])
            dt = datetime.fromisoformat(ts_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            transactions.append(
                {
                    "txn_id": str(r[0]),
                    "sender_account_id": str(r[1]),
                    "receiver_account_id": str(r[2]),
                    "sender_vpa": str(r[3]),
                    "receiver_vpa": str(r[4]),
                    "amount_paise": int(r[5]),
                    "amount_inr": float(r[6]),
                    "raw_timestamp": str(r[7]),
                    "timestamp_utc": ts_str,
                    "dt": dt,
                    "device_id": str(r[9]) if r[9] else None,
                }
            )

        # Index transactions by sender for fast path exploration
        by_sender: dict[str, list[dict[str, Any]]] = {}
        for txn in transactions:
            by_sender.setdefault(txn["sender_account_id"], []).append(txn)

        found_cycles: list[list[dict[str, Any]]] = []
        seen_cycle_txns: set[tuple[str, ...]] = set()

        def dfs(
            path: list[dict[str, Any]],
            current_account: str,
            origin_account: str,
            start_dt: datetime,
            last_dt: datetime,
            last_amount: float,
        ) -> None:
            if len(path) >= max_cycle_len:
                return

            candidates = by_sender.get(current_account, [])
            for t_next in candidates:
                # Avoid reusing transaction already in current path
                if any(t["txn_id"] == t_next["txn_id"] for t in path):
                    continue

                # Enforce chronological sequence
                delay_sec = (t_next["dt"] - last_dt).total_seconds()
                if delay_sec < 0:
                    continue

                # Enforce overall time window
                elapsed_sec = (t_next["dt"] - start_dt).total_seconds()
                if elapsed_sec > max_duration_sec:
                    continue

                # Filter trivial amounts
                if t_next["amount_inr"] < min_amount:
                    continue

                # Enforce amount retention between consecutive hops
                ratio = t_next["amount_inr"] / last_amount if last_amount > 0 else 0.0
                if not (min_ratio <= ratio <= max_ratio):
                    continue

                target_account = t_next["receiver_account_id"]
                new_path = path + [t_next]

                if target_account == origin_account:
                    # Directed cycle closed!
                    if len(new_path) >= min_cycle_len:
                        # Deduplicate across different starting perspectives
                        canonical_txn_key = tuple(sorted(t["txn_id"] for t in new_path))
                        if canonical_txn_key not in seen_cycle_txns:
                            seen_cycle_txns.add(canonical_txn_key)
                            found_cycles.append(new_path)
                else:
                    # Ensure intermediate account is not visited multiple times (no figure-8s)
                    visited_senders = {t["sender_account_id"] for t in new_path}
                    if target_account not in visited_senders:
                        dfs(
                            path=new_path,
                            current_account=target_account,
                            origin_account=origin_account,
                            start_dt=start_dt,
                            last_dt=t_next["dt"],
                            last_amount=t_next["amount_inr"],
                        )

        # Explore cycles originating from each candidate transaction
        for t0 in transactions:
            if t0["amount_inr"] < min_amount:
                continue
            dfs(
                path=[t0],
                current_account=t0["receiver_account_id"],
                origin_account=t0["sender_account_id"],
                start_dt=t0["dt"],
                last_dt=t0["dt"],
                last_amount=t0["amount_inr"],
            )

        # Build alerts for discovered cycles
        alerts: list[DetectionAlert] = []
        for cycle_txns in found_cycles:
            alert = self._create_cycle_alert(
                cycle_txns=cycle_txns,
                complaints_by_txn=complaints_by_txn,
                complaints_by_acc=complaints_by_acc,
                accounts_map=accounts_map,
            )
            alerts.append(alert)

        return alerts

    def _create_cycle_alert(
        self,
        cycle_txns: list[dict[str, Any]],
        complaints_by_txn: dict[str, list[str]],
        complaints_by_acc: dict[str, list[str]],
        accounts_map: dict[str, dict[str, Any]],
    ) -> DetectionAlert:
        """Construct a structured DetectionAlert for a detected cycle."""
        # Participating accounts in ordered sequence
        ordered_account_ids = [t["sender_account_id"] for t in cycle_txns]
        vpas = [
            accounts_map.get(acc, {}).get("vpa", "")
            for acc in ordered_account_ids
        ]
        txn_ids = [t["txn_id"] for t in cycle_txns]

        start_amt = cycle_txns[0]["amount_inr"]
        end_amt = cycle_txns[-1]["amount_inr"]
        start_dt = cycle_txns[0]["dt"]
        end_dt = cycle_txns[-1]["dt"]
        total_elapsed_sec = (end_dt - start_dt).total_seconds()
        retention_ratio = end_amt / start_amt if start_amt > 0 else 0.0

        # Build hop evidences
        hop_evidences: list[HopEvidence] = []
        for i in range(len(cycle_txns)):
            t_curr = cycle_txns[i]
            t_next = cycle_txns[(i + 1) % len(cycle_txns)]
            delay = (
                (t_next["dt"] - t_curr["dt"]).total_seconds()
                if i < len(cycle_txns) - 1
                else 0.0
            )
            ratio = (
                t_next["amount_inr"] / t_curr["amount_inr"]
                if t_curr["amount_inr"] > 0
                else 0.0
            )
            hop_evidences.append(
                HopEvidence(
                    incoming_txn_id=t_curr["txn_id"],
                    incoming_timestamp_utc=t_curr["timestamp_utc"],
                    incoming_amount_inr=t_curr["amount_inr"],
                    outgoing_txn_id=t_next["txn_id"],
                    outgoing_timestamp_utc=t_next["timestamp_utc"],
                    outgoing_amount_inr=t_next["amount_inr"],
                    delay_seconds=round(max(0.0, delay), 1),
                    delay_minutes=round(max(0.0, delay) / 60.0, 2),
                    forwarding_ratio=round(ratio, 4),
                    forwarding_percentage=round(ratio * 100.0, 2),
                    source_account_id=t_curr["sender_account_id"],
                    source_vpa=t_curr["sender_vpa"],
                    intermediary_account_id=t_curr["receiver_account_id"],
                    intermediary_vpa=t_curr["receiver_vpa"],
                    destination_account_id=t_next["receiver_account_id"],
                    destination_vpa=t_next["receiver_vpa"],
                )
            )

        # Linked complaints
        linked_complaints: set[str] = set()
        for t_id in txn_ids:
            linked_complaints.update(complaints_by_txn.get(t_id, []))
        for acc_id in ordered_account_ids:
            linked_complaints.update(complaints_by_acc.get(acc_id, []))

        evidence_payload: dict[str, Any] = {
            "pattern": self.rule_id,
            "cycle_length": len(ordered_account_ids),
            "start_amount_inr": start_amt,
            "end_amount_inr": end_amt,
            "amount_retention_ratio": round(retention_ratio, 4),
            "amount_retention_percentage": round(retention_ratio * 100.0, 2),
            "duration_seconds": round(total_elapsed_sec, 1),
            "duration_minutes": round(total_elapsed_sec / 60.0, 2),
            "duration_hours": round(total_elapsed_sec / 3600.0, 2),
            "hops": [h.model_dump() for h in hop_evidences],
            "transactions": [
                {
                    "txn_id": t["txn_id"],
                    "sender_account_id": t["sender_account_id"],
                    "receiver_account_id": t["receiver_account_id"],
                    "amount_inr": t["amount_inr"],
                    "timestamp_utc": t["timestamp_utc"],
                }
                for t in cycle_txns
            ],
        }

        # Deterministic Alert ID based on canonical sorted txn IDs
        canonical_txns_str = ":".join(sorted(txn_ids))
        hash_input = f"{self.rule_id}:{canonical_txns_str}"
        alert_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()[:12]
        alert_id = f"alt_cyc_{alert_hash}"

        # Title and Priority
        priority = "CRITICAL" if (start_amt >= 100000.0 or len(linked_complaints) > 0) else "HIGH"
        title = f"Circular Transaction Cycle ({len(ordered_account_ids)} accounts)"

        # Explainable narrative
        flow_str = " -> ".join(ordered_account_ids) + f" -> {ordered_account_ids[0]}"
        elapsed_min = total_elapsed_sec / 60.0
        retention_pct = retention_ratio * 100.0
        explanation = (
            f"Circular fund movement detected across {len(ordered_account_ids)} accounts "
            f"({flow_str}) through {len(txn_ids)} transactions within {elapsed_min:.1f} minutes. "
            f"Initial outflow of Rs {start_amt:,.2f} returned Rs {end_amt:,.2f} "
            f"({retention_pct:.1f}% retained). Rapid circular velocity without economic rationale "
            f"is characteristic of artificial transaction volume inflation or circular routing."
        )

        limitations = [
            (
                "Automated cycle detection identifies closed transfer paths "
                "but does not prove fraudulent intent."
            ),
            (
                "Legitimate multi-party expense sharing or reciprocal group settlements "
                "over short horizons may present circular topology."
            ),
            (
                "Detection is sensitive to configured duration window, "
                "cycle length, and retention ratio boundaries."
            ),
        ]

        alternative_explanations = [
            (
                "Multi-party personal expense settlement, dining bill splitting, "
                "or shared accommodation cost rebalancing."
            ),
            (
                "Circular trade payments, vendor advances, or contractor settlement loops "
                "with customary fee deductions."
            ),
            (
                "Internal treasury rebalancing between multiple accounts or corporate entities "
                "under common control."
            ),
        ]

        # Calculate replaceable score (scoring pending Aryan formula)
        score = calculate_alert_score(self.rule_id, evidence_payload)

        # Build lightweight graph context for visual rendering
        graph_nodes = [
            {"id": f"acc:{acc}", "label": acc, "node_type": "account"}
            for acc in ordered_account_ids
        ]
        graph_edges = [
            {
                "id": f"txn:{t['txn_id']}",
                "source": f"acc:{t['sender_account_id']}",
                "target": f"acc:{t['receiver_account_id']}",
                "edge_type": "transaction",
            }
            for t in cycle_txns
        ]
        graph_context = {"nodes": graph_nodes, "edges": graph_edges}

        return DetectionAlert(
            alert_id=alert_id,
            rule_id=self.rule_id,
            title=title,
            priority=priority,
            score=score,
            account_ids=ordered_account_ids,
            vpas=vpas,
            txn_ids=txn_ids,
            evidence=evidence_payload,
            explanation=explanation,
            limitations=limitations,
            alternative_explanations=alternative_explanations,
            complaint_ids=sorted(linked_complaints),
            related_alert_ids=[],
            ring_id=None,
            graph_context=graph_context,
        )
