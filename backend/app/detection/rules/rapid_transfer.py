"""Rapid onward fund transfer detection rule.

Detects accounts acting as rapid forwarding intermediaries / mules that receive funds
and quickly transfer a significant proportion onward within a tight time window.
"""

import hashlib
from datetime import datetime, timezone
from typing import Any, Optional

from app.detection.base import BaseDetectionRule
from app.detection.models import DetectionAlert, HopEvidence
from app.detection.scoring import calculate_alert_score


class RapidOnwardTransferRule(BaseDetectionRule):
    """Detection rule for rapid pass-through and onward fund transfers."""

    rule_id: str = "RAPID_ONWARD_TRANSFER"
    title: str = "Rapid Onward Fund Transfer"
    default_priority: str = "HIGH"

    def detect(
        self,
        conn: Any,
        config: Optional[dict[str, Any]] = None,
    ) -> list[DetectionAlert]:
        """Execute detection for rapid onward transfer chains.

        Configurable Parameters:
            max_delay_seconds (int): Maximum time between inflow and outflow
                (default: 1800s / 30m).
            min_forwarding_ratio (float): Minimum outflow/inflow amount ratio
                (default: 0.80 / 80%).
            max_forwarding_ratio (float): Maximum outflow/inflow amount ratio
                (default: 1.05 / 105%).
            min_amount_inr (float): Minimum transaction amount in INR to evaluate
                (default: 1000.0).
            min_hops (int): Minimum forwarding hops to generate an alert (default: 1).
        """
        cfg = config or {}
        max_delay_sec = int(cfg.get("max_delay_seconds", 1800))
        min_ratio = float(cfg.get("min_forwarding_ratio", 0.80))
        max_ratio = float(cfg.get("max_forwarding_ratio", 1.05))
        min_amount = float(cfg.get("min_amount_inr", 1000.0))
        min_hops = int(cfg.get("min_hops", 1))

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

        # 2. Index inflows and outflows by account
        inflows_by_acc: dict[str, list[dict[str, Any]]] = {}
        for txn in transactions:
            inflows_by_acc.setdefault(txn["receiver_account_id"], []).append(txn)

        # 3. Find candidate forwarding hops (inflow -> intermediary -> outflow)
        hops: list[dict[str, Any]] = []
        consumed_inflows: set[str] = set()

        for t_out in transactions:
            intermediary = t_out["sender_account_id"]
            out_amt = t_out["amount_inr"]
            out_dt = t_out["dt"]

            candidate_inflows = inflows_by_acc.get(intermediary, [])
            best_match: Optional[dict[str, Any]] = None
            best_delay: float = float("inf")

            for t_in in reversed(candidate_inflows):
                if t_in["txn_id"] in consumed_inflows:
                    continue
                if t_in["txn_id"] == t_out["txn_id"]:
                    continue
                # Skip direct reciprocal refund back to same sender
                if t_in["sender_account_id"] == t_out["receiver_account_id"]:
                    continue

                in_amt = t_in["amount_inr"]
                in_dt = t_in["dt"]

                if in_amt < min_amount:
                    continue

                delay = (out_dt - in_dt).total_seconds()
                if 0 <= delay <= max_delay_sec:
                    ratio = out_amt / in_amt
                    if min_ratio <= ratio <= max_ratio:
                        if delay < best_delay:
                            best_match = t_in
                            best_delay = delay
                            # Since candidate_inflows is traversed in reverse (closest first),
                            # break early once we have the most recent matching inflow
                            break

            if best_match is not None:
                consumed_inflows.add(best_match["txn_id"])
                ratio = out_amt / best_match["amount_inr"]
                hops.append(
                    {
                        "in_txn": best_match,
                        "out_txn": t_out,
                        "intermediary": intermediary,
                        "delay_seconds": best_delay,
                        "forwarding_ratio": ratio,
                    }
                )

        # 4. Chain contiguous hops (where Hop A's out_txn is Hop B's in_txn)
        chains = self._build_chains(hops)

        # 5. Build detection alerts for chains meeting min_hops
        alerts: list[DetectionAlert] = []
        for chain in chains:
            if len(chain) < min_hops:
                continue

            alert = self._create_chain_alert(
                chain=chain,
                complaints_by_txn=complaints_by_txn,
                complaints_by_acc=complaints_by_acc,
                accounts_map=accounts_map,
            )
            alerts.append(alert)

        return alerts

    def _build_chains(self, hops: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
        """Assemble contiguous multi-hop transfer chains from individual hops."""
        # Map: in_txn_id -> hop
        by_in_txn: dict[str, dict[str, Any]] = {h["in_txn"]["txn_id"]: h for h in hops}
        # Outflow txn IDs that start a subsequent hop
        chained_inflow_txns = set(by_in_txn.keys())

        # Find starting hops (hops whose in_txn was not generated by an earlier hop)
        visited_hops: set[int] = set()
        chains: list[list[dict[str, Any]]] = []

        # Start with root hops
        for idx, h in enumerate(hops):
            # If h's in_txn is NOT the out_txn of some other hop, it is a chain root
            is_root = not any(other["out_txn"]["txn_id"] == h["in_txn"]["txn_id"] for other in hops)
            if is_root and idx not in visited_hops:
                chain = [h]
                visited_hops.add(idx)
                curr_hop = h
                while curr_hop["out_txn"]["txn_id"] in chained_inflow_txns:
                    next_hop = by_in_txn[curr_hop["out_txn"]["txn_id"]]
                    next_idx = hops.index(next_hop)
                    if next_idx in visited_hops:
                        break  # Prevent cycle loop
                    visited_hops.add(next_idx)
                    chain.append(next_hop)
                    curr_hop = next_hop
                chains.append(chain)

        # Handle any remaining hops (e.g. within pure cycles)
        for idx, h in enumerate(hops):
            if idx not in visited_hops:
                chain = [h]
                visited_hops.add(idx)
                curr_hop = h
                while curr_hop["out_txn"]["txn_id"] in chained_inflow_txns:
                    next_hop = by_in_txn[curr_hop["out_txn"]["txn_id"]]
                    next_idx = hops.index(next_hop)
                    if next_idx in visited_hops:
                        break
                    visited_hops.add(next_idx)
                    chain.append(next_hop)
                    curr_hop = next_hop
                chains.append(chain)

        return chains

    def _create_chain_alert(
        self,
        chain: list[dict[str, Any]],
        complaints_by_txn: dict[str, list[str]],
        complaints_by_acc: dict[str, list[str]],
        accounts_map: dict[str, dict[str, Any]],
    ) -> DetectionAlert:
        """Create a fully-formed DetectionAlert from a chain of forwarding hops."""
        first_hop = chain[0]
        last_hop = chain[-1]

        # Collect unique ordered accounts along the chain
        account_ids: list[str] = [first_hop["in_txn"]["sender_account_id"]]
        for h in chain:
            account_ids.append(h["intermediary"])
        account_ids.append(last_hop["out_txn"]["receiver_account_id"])

        # Deduplicate while preserving order
        ordered_account_ids: list[str] = []
        for acc in account_ids:
            if acc not in ordered_account_ids:
                ordered_account_ids.append(acc)

        # Resolve VPAs
        vpas: list[str] = [
            accounts_map.get(acc, {}).get("vpa", f"{acc}@unknown")
            for acc in ordered_account_ids
        ]

        # Collect chronological transaction IDs
        txn_ids: list[str] = [first_hop["in_txn"]["txn_id"]]
        for h in chain:
            if h["out_txn"]["txn_id"] not in txn_ids:
                txn_ids.append(h["out_txn"]["txn_id"])

        # Collect complaints
        linked_complaints: set[str] = set()
        for t_id in txn_ids:
            linked_complaints.update(complaints_by_txn.get(t_id, []))
        for acc_id in ordered_account_ids:
            linked_complaints.update(complaints_by_acc.get(acc_id, []))

        # Build detailed hop evidence
        hop_evidences: list[HopEvidence] = []
        for h in chain:
            in_t = h["in_txn"]
            out_t = h["out_txn"]
            delay = h["delay_seconds"]
            ratio = h["forwarding_ratio"]
            hop_evidences.append(
                HopEvidence(
                    incoming_txn_id=in_t["txn_id"],
                    incoming_timestamp_utc=in_t["timestamp_utc"],
                    incoming_amount_inr=in_t["amount_inr"],
                    outgoing_txn_id=out_t["txn_id"],
                    outgoing_timestamp_utc=out_t["timestamp_utc"],
                    outgoing_amount_inr=out_t["amount_inr"],
                    delay_seconds=round(delay, 1),
                    delay_minutes=round(delay / 60.0, 2),
                    forwarding_ratio=round(ratio, 4),
                    forwarding_percentage=round(ratio * 100.0, 2),
                    source_account_id=in_t["sender_account_id"],
                    source_vpa=in_t["sender_vpa"],
                    intermediary_account_id=h["intermediary"],
                    intermediary_vpa=in_t["receiver_vpa"],
                    destination_account_id=out_t["receiver_account_id"],
                    destination_vpa=out_t["receiver_vpa"],
                )
            )

        initial_amt = first_hop["in_txn"]["amount_inr"]
        final_amt = last_hop["out_txn"]["amount_inr"]
        total_time_sec = (last_hop["out_txn"]["dt"] - first_hop["in_txn"]["dt"]).total_seconds()
        overall_ratio = final_amt / initial_amt if initial_amt > 0 else 0.0

        evidence_payload = {
            "pattern": "RAPID_ONWARD_TRANSFER",
            "hop_count": len(chain),
            "account_count": len(ordered_account_ids),
            "initial_amount_inr": initial_amt,
            "final_amount_inr": final_amt,
            "overall_forwarding_ratio": round(overall_ratio, 4),
            "overall_forwarding_percentage": round(overall_ratio * 100.0, 2),
            "total_elapsed_seconds": round(total_time_sec, 1),
            "total_elapsed_minutes": round(total_time_sec / 60.0, 2),
            "hops": [h.model_dump() for h in hop_evidences],
        }

        # Priority & Title
        if len(chain) >= 2 or initial_amt >= 50000.0:
            priority = "HIGH"
            title = f"Multi-Hop Rapid Transfer Chain ({len(chain)} hops)"
        else:
            priority = "MEDIUM"
            title = "Rapid Onward Fund Transfer"

        # Deterministic Alert ID
        hash_input = f"{self.rule_id}:" + ":".join(txn_ids)
        alert_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()[:12]
        alert_id = f"alt_rot_{alert_hash}"

        # Explainable Narrative
        if len(chain) > 1:
            intermediaries_str = " -> ".join(ordered_account_ids)
            pcts = [f"{h.forwarding_percentage:.1f}%" for h in hop_evidences]
            pcts_str = ", ".join(pcts)
            total_min = total_time_sec / 60.0
            explanation = (
                f"Multi-hop rapid fund dissipation detected across "
                f"{len(ordered_account_ids)} accounts ({intermediaries_str}) "
                f"through {len(txn_ids)} transactions totaling Rs {initial_amt:,.2f} "
                f"entering and Rs {final_amt:,.2f} exiting within {total_min:.1f} minutes. "
                f"Consecutive forwarding proportions: [{pcts_str}]."
            )
        else:
            hop = hop_evidences[0]
            explanation = (
                f"Intermediary account {hop.intermediary_account_id} received "
                f"Rs {hop.incoming_amount_inr:,.2f} from {hop.source_account_id} "
                f"and rapidly forwarded Rs {hop.outgoing_amount_inr:,.2f} "
                f"({hop.forwarding_percentage:.1f}%) to {hop.destination_account_id} "
                f"within {hop.delay_minutes:.1f} minutes."
            )

        limitations = [
            (
                "Automated pattern detection highlights operational characteristics "
                "but does not prove fraudulent intent."
            ),
            (
                "Legitimate high-velocity payment processors, payroll splitters, "
                "or merchant settlements may exhibit rapid turnaround."
            ),
            "Detection is sensitive to configured time window and forwarding ratio parameters.",
        ]

        alternative_explanations = [
            "Immediate invoice or supplier payment triggered upon receipt of customer funds.",
            "Personal expense reimbursement, split bill settlement, or peer-to-peer pass-through.",
            "Automated bank balance sweeping or multi-wallet replenishment.",
        ]

        # Calculate replaceable score (scoring pending Aryan formula)
        score = calculate_alert_score(self.rule_id, evidence_payload)

        # Build lightweight graph context for visual rendering
        graph_nodes = [
            {"id": f"acc:{acc}", "label": acc, "node_type": "account"}
            for acc in ordered_account_ids
        ]
        graph_edges = []
        if hop_evidences:
            first_h = hop_evidences[0]
            graph_edges.append(
                {
                    "id": f"txn:{first_h.incoming_txn_id}",
                    "source": f"acc:{first_h.source_account_id}",
                    "target": f"acc:{first_h.intermediary_account_id}",
                    "edge_type": "transaction",
                }
            )
            for h in hop_evidences:
                graph_edges.append(
                    {
                        "id": f"txn:{h.outgoing_txn_id}",
                        "source": f"acc:{h.intermediary_account_id}",
                        "target": f"acc:{h.destination_account_id}",
                        "edge_type": "transaction",
                    }
                )
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
