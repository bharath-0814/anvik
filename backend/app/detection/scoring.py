"""Scoring interface for Anvik fraud detection alerts.

NOTE: Aryan (Member 4) is currently developing the finalized multi-factor scoring formula.
Scoring in this module is intentionally modular, replaceable, and heuristic.
Scores represent investigative prioritization indicators, NOT calibrated fraud probabilities
or assertions of guilt.
"""

from typing import Any, Optional


def calculate_alert_score(
    rule_id: str,
    evidence: dict[str, Any],
    base_score: Optional[float] = None,
) -> float:
    """Calculate an initial prioritization score for a detection alert.

    Args:
        rule_id: Rule identifier (e.g. 'RAPID_ONWARD_TRANSFER').
        evidence: Quantitative evidence dictionary extracted by the detector.
        base_score: Optional caller-specified baseline override.

    Returns:
        float: Priority score bounded in [0.0, 100.0].
    """
    if base_score is not None:
        return max(0.0, min(100.0, float(base_score)))

    # Placeholder baseline prioritization while Aryan finalizes the formula
    rule_key = rule_id.upper()
    if rule_key == "RAPID_ONWARD_TRANSFER":
        # Heuristic prioritization based on chain length and forwarded ratio
        hops = evidence.get("hop_count", 1)
        ratio = evidence.get("overall_forwarding_ratio", 0.9)
        # Multi-hop rapid transfers receive higher triage urgency
        base = 70.0 + min(20.0, (hops - 1) * 10.0) + (ratio * 10.0)
        return round(max(0.0, min(100.0, base)), 2)
    elif rule_key == "TRANSACTION_CYCLE":
        # Heuristic prioritization based on cycle length, velocity and retention
        cycle_len = evidence.get("cycle_length", 3)
        duration_mins = evidence.get("duration_minutes", 60.0)
        retention = evidence.get("amount_retention_ratio", 0.95)
        # Fast cycles with tight loops receive higher triage urgency
        speed_bonus = max(0.0, min(10.0, (240.0 - duration_mins) / 24.0))
        retention_bonus = max(0.0, min(10.0, retention * 10.0))
        base = 75.0 + min(10.0, (cycle_len - 3) * 5.0) + speed_bonus + retention_bonus
        return round(max(0.0, min(100.0, base)), 2)

    return 50.0
