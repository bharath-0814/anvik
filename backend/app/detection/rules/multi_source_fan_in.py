"""Multiple-source fan-in detection rule.

Detects an account receiving incoming funds from multiple distinct senders
within a concentrated time window, characteristic of mule account collection,
unauthorized payment pooling, or investment scam consolidation.
"""

import hashlib
from datetime import datetime, timezone
from typing import Any, Optional

from app.detection.base import BaseDetectionRule
from app.detection.models import DetectionAlert, HopEvidence
from app.detection.scoring import calculate_alert_score


class MultipleIncomingSourcesRule(BaseDetectionRule):
    """Detection rule for multiple-source fan-in fund consolidation."""

    rule_id: str = "multiple_incoming_sources"
    aliases: list[str] = ["MULTIPLE_SOURCE_FAN_IN", "multiple_source_fan_in"]
    title: str = "Multiple-Source Fan-In"
    default_priority: str = "HIGH"

    def detect(
        self,
        conn: Any,
        config: Optional[dict[str, Any]] = None,
    ) -> list[DetectionAlert]:
        """Execute detection for multiple-source fan-in consolidation.

        Configurable Parameters:
            time_window_hours (float): Maximum time window in hours to evaluate
                inflows (default: 3.0 hours).
            min_distinct_senders (int): Minimum number of distinct sender accounts
                required to trigger an alert (default: 10).
            min_amount_inr (float): Minimum individual transaction amount in INR
                to consider (default: 100.0).
            min_total_volume_inr (float): Minimum aggregate volume across the burst
                (default: 0.0).
        """
        cfg = config or {}
        time_window_sec = float(cfg.get("time_window_hours", 3.0)) * 3600.0
        min_senders = int(cfg.get("min_distinct_senders", 10))
        min_amount = float(cfg.get("min_amount_inr", 100.0))
        min_total_volume = float(cfg.get("min_total_volume_inr", 0.0))

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

        # 2. Group incoming transactions by receiver account
        inflows_by_receiver: dict[str, list[dict[str, Any]]] = {}
        for txn in transactions:
            if txn["amount_inr"] >= min_amount:
                inflows_by_receiver.setdefault(txn["receiver_account_id"], []).append(txn)

        alerts: list[DetectionAlert] = []

        # 3. For each receiver, detect candidate fan-in bursts via sliding window
        for receiver_acc, incoming in inflows_by_receiver.items():
            if len(incoming) < min_senders:
                continue

            # Identify all windows meeting the distinct sender threshold
            qualifying_windows: list[tuple[int, int, list[dict[str, Any]]]] = []
            n = len(incoming)
            for i in range(n):
                t_start = incoming[i]
                w_txns: list[dict[str, Any]] = []
                senders: set[str] = set()
                for j in range(i, n):
                    t_curr = incoming[j]
                    if (t_curr["dt"] - t_start["dt"]).total_seconds() <= time_window_sec:
                        senders.add(t_curr["sender_account_id"])
                        w_txns.append(t_curr)
                    else:
                        break
                if len(senders) >= min_senders:
                    qualifying_windows.append((i, i + len(w_txns) - 1, w_txns))

            if not qualifying_windows:
                continue

            # Merge overlapping windows into maximal contiguous bursts
            merged_bursts: list[list[dict[str, Any]]] = []
            current_txns = list(qualifying_windows[0][2])
            current_end_idx = qualifying_windows[0][1]

            for start_idx, end_idx, w_txns in qualifying_windows[1:]:
                if start_idx <= current_end_idx:
                    seen_ids = {t["txn_id"] for t in current_txns}
                    for t in w_txns:
                        if t["txn_id"] not in seen_ids:
                            current_txns.append(t)
                            seen_ids.add(t["txn_id"])
                    current_end_idx = max(current_end_idx, end_idx)
                else:
                    merged_bursts.append(current_txns)
                    current_txns = list(w_txns)
                    current_end_idx = end_idx
            merged_bursts.append(current_txns)

            # Build alerts for each merged burst meeting criteria
            for burst_txns in merged_bursts:
                distinct_senders = {t["sender_account_id"] for t in burst_txns}
                total_volume = sum(t["amount_inr"] for t in burst_txns)

                if len(distinct_senders) < min_senders:
                    continue
                if total_volume < min_total_volume:
                    continue

                alert = self._create_fan_in_alert(
                    receiver_acc=receiver_acc,
                    burst_txns=burst_txns,
                    distinct_senders=distinct_senders,
                    complaints_by_txn=complaints_by_txn,
                    complaints_by_acc=complaints_by_acc,
                    accounts_map=accounts_map,
                )
                alerts.append(alert)

        return alerts

    def _create_fan_in_alert(
        self,
        receiver_acc: str,
        burst_txns: list[dict[str, Any]],
        distinct_senders: set[str],
        complaints_by_txn: dict[str, list[str]],
        complaints_by_acc: dict[str, list[str]],
        accounts_map: dict[str, dict[str, Any]],
    ) -> DetectionAlert:
        """Construct a structured DetectionAlert for a fan-in burst."""
        # Chronological ordering of transactions
        burst_txns_sorted = sorted(burst_txns, key=lambda t: t["dt"])
        txn_ids = [t["txn_id"] for t in burst_txns_sorted]

        # Accounts: Collector account first, followed by distinct senders
        ordered_account_ids = [receiver_acc] + sorted(distinct_senders)
        vpas = [accounts_map.get(acc, {}).get("vpa", "") for acc in ordered_account_ids]

        amounts = [t["amount_inr"] for t in burst_txns_sorted]
        total_amt = sum(amounts)
        min_amt = min(amounts)
        max_amt = max(amounts)
        avg_amt = total_amt / len(amounts) if amounts else 0.0

        start_dt = burst_txns_sorted[0]["dt"]
        end_dt = burst_txns_sorted[-1]["dt"]
        duration_sec = (end_dt - start_dt).total_seconds()
        duration_min = duration_sec / 60.0
        duration_hrs = duration_sec / 3600.0

        # Linked complaints
        linked_complaints: set[str] = set()
        for t_id in txn_ids:
            linked_complaints.update(complaints_by_txn.get(t_id, []))
        for acc_id in ordered_account_ids:
            linked_complaints.update(complaints_by_acc.get(acc_id, []))

        # Build hop evidences for each incoming payment to the collector
        hop_evidences: list[HopEvidence] = []
        for t in burst_txns_sorted:
            hop_evidences.append(
                HopEvidence(
                    incoming_txn_id=t["txn_id"],
                    incoming_timestamp_utc=t["timestamp_utc"],
                    incoming_amount_inr=t["amount_inr"],
                    outgoing_txn_id="",
                    outgoing_timestamp_utc="",
                    outgoing_amount_inr=0.0,
                    delay_seconds=0.0,
                    delay_minutes=0.0,
                    forwarding_ratio=1.0,
                    forwarding_percentage=100.0,
                    source_account_id=t["sender_account_id"],
                    source_vpa=t["sender_vpa"],
                    intermediary_account_id=receiver_acc,
                    intermediary_vpa=t["receiver_vpa"],
                    destination_account_id=receiver_acc,
                    destination_vpa=t["receiver_vpa"],
                )
            )

        evidence_payload: dict[str, Any] = {
            "pattern": self.rule_id,
            "destination_account_id": receiver_acc,
            "destination_vpa": accounts_map.get(receiver_acc, {}).get("vpa", ""),
            "distinct_sender_count": len(distinct_senders),
            "transaction_count": len(burst_txns_sorted),
            "total_amount_inr": round(total_amt, 2),
            "min_amount_inr": round(min_amt, 2),
            "max_amount_inr": round(max_amt, 2),
            "avg_amount_inr": round(avg_amt, 2),
            "duration_seconds": round(duration_sec, 1),
            "duration_minutes": round(duration_min, 2),
            "duration_hours": round(duration_hrs, 2),
            "hops": [h.model_dump() for h in hop_evidences],
            "transactions": [
                {
                    "txn_id": t["txn_id"],
                    "sender_account_id": t["sender_account_id"],
                    "sender_vpa": t["sender_vpa"],
                    "amount_inr": t["amount_inr"],
                    "timestamp_utc": t["timestamp_utc"],
                }
                for t in burst_txns_sorted
            ],
        }

        # Deterministic Alert ID based on canonical receiver and sorted transaction IDs
        canonical_txns_str = ":".join(sorted(txn_ids))
        hash_input = f"{self.rule_id}:{receiver_acc}:{canonical_txns_str}"
        alert_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()[:12]
        alert_id = f"alt_fanin_{alert_hash}"

        # Severity Priority
        if len(distinct_senders) >= 25 or total_amt >= 100000.0 or len(linked_complaints) > 0:
            priority = "CRITICAL"
        elif len(distinct_senders) >= 15:
            priority = "HIGH"
        else:
            priority = "MEDIUM"

        title = f"Multiple-Source Fan-In ({len(distinct_senders)} senders)"

        # Explainable narrative
        explanation = (
            f"High-velocity fan-in consolidation detected: account {receiver_acc} received "
            f"{len(burst_txns_sorted)} transactions from {len(distinct_senders)} distinct senders "
            f"totaling Rs {total_amt:,.2f} within {duration_min:.1f} minutes "
            f"(average Rs {avg_amt:,.2f} per transaction). Rapid aggregation from numerous "
            f"unrelated accounts without corresponding commercial disbursement is characteristic "
            f"of mule collection, investment scam pooling, or unauthorized payment aggregation."
        )

        limitations = [
            (
                "Automated fan-in detection identifies high-velocity multi-party inflow patterns "
                "but does not prove fraudulent intent."
            ),
            (
                "Legitimate community fundraising campaigns, event ticket pooling, institutional "
                "collections, or religious donations can exhibit similar convergence topologies."
            ),
            (
                "Detection is sensitive to configured time window duration, "
                "distinct sender threshold, and minimum amount parameters."
            ),
        ]

        alternative_explanations = [
            (
                "Legitimate charity drive, crowdfunding campaign, disaster relief appeal, "
                "or community fundraising."
            ),
            (
                "Social event ticketing, group wedding gift pooling, college reunion collection, "
                "or shared trip booking."
            ),
            (
                "Informal chit-fund contribution collection, self-help group deposits, "
                "or religious donation collections."
            ),
            (
                "Small merchant or street vendor receiving diverse customer UPI micro-payments "
                "during peak operating hours."
            ),
        ]

        # Calculate replaceable score (scoring pending Aryan formula)
        score = calculate_alert_score(self.rule_id, evidence_payload)

        # Build lightweight graph context for visual rendering
        graph_nodes = [
            {
                "id": f"acc:{receiver_acc}",
                "label": receiver_acc,
                "node_type": "account",
                "role": "collector",
            }
        ]
        for s in sorted(distinct_senders):
            graph_nodes.append(
                {
                    "id": f"acc:{s}",
                    "label": s,
                    "node_type": "account",
                    "role": "sender",
                }
            )

        graph_edges = [
            {
                "id": f"txn:{t['txn_id']}",
                "source": f"acc:{t['sender_account_id']}",
                "target": f"acc:{receiver_acc}",
                "amount_inr": t["amount_inr"],
                "edge_type": "transaction",
            }
            for t in burst_txns_sorted
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


# Backward-compatible and descriptive alias
MultiSourceFanInRule = MultipleIncomingSourcesRule
