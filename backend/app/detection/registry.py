"""Central registry for discovering and executing fraud detection rules."""

from typing import Any, Optional

from app.detection.base import BaseDetectionRule
from app.detection.models import DetectionAlert


class RuleRegistry:
    """Registry coordinating detection rules and batch execution."""

    def __init__(self) -> None:
        self._rules: dict[str, BaseDetectionRule] = {}

    def register(self, rule: BaseDetectionRule) -> None:
        """Register a detection rule instance.

        Keys are indexed both uppercase and lowercase for convenience.
        """
        self._rules[rule.rule_id.upper()] = rule

    def get(self, rule_id: str) -> Optional[BaseDetectionRule]:
        """Look up a registered rule by ID (case-insensitive)."""
        return self._rules.get(rule_id.upper())

    def list_rules(self) -> list[BaseDetectionRule]:
        """Return all uniquely registered rules."""
        return list(self._rules.values())

    def run_rule(
        self,
        rule_id: str,
        conn: Any,
        config: Optional[dict[str, Any]] = None,
    ) -> list[DetectionAlert]:
        """Execute a specific detection rule by ID."""
        rule = self.get(rule_id)
        if not rule:
            available = ", ".join(self._rules.keys())
            raise ValueError(f"Unknown detection rule '{rule_id}'. Available: [{available}]")
        return rule.detect(conn, config=config)

    def run_all(
        self,
        conn: Any,
        configs: Optional[dict[str, dict[str, Any]]] = None,
    ) -> list[DetectionAlert]:
        """Execute all registered detection rules in order and aggregate alerts."""
        alerts: list[DetectionAlert] = []
        cfg_map = configs or {}
        for rule_key, rule in self._rules.items():
            rule_cfg = cfg_map.get(rule_key) or cfg_map.get(rule_key.lower())
            findings = rule.detect(conn, config=rule_cfg)
            alerts.extend(findings)
        return alerts


def get_default_registry() -> RuleRegistry:
    """Build and return a RuleRegistry populated with standard detection rules."""
    reg = RuleRegistry()
    from app.detection.rules.rapid_transfer import RapidOnwardTransferRule
    from app.detection.rules.transaction_cycle import TransactionCycleRule

    reg.register(RapidOnwardTransferRule())
    reg.register(TransactionCycleRule())
    return reg


# Global singleton instance with default rules registered
registry = get_default_registry()

