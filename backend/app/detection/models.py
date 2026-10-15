"""Data models for fraud detection alerts, evidence, and rule configurations."""

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class HopEvidence(BaseModel):
    """Detailed evidence for an individual rapid forwarding hop."""

    incoming_txn_id: str
    incoming_timestamp_utc: str
    incoming_amount_inr: float
    outgoing_txn_id: str
    outgoing_timestamp_utc: str
    outgoing_amount_inr: float
    delay_seconds: float
    delay_minutes: float
    forwarding_ratio: float
    forwarding_percentage: float
    source_account_id: str
    source_vpa: str
    intermediary_account_id: str
    intermediary_vpa: str
    destination_account_id: str
    destination_vpa: str


class DetectionAlert(BaseModel):
    """Investigative alert record compatible with UI graph and case management."""

    alert_id: str = Field(..., description="Unique deterministic alert identifier")
    rule_id: str = Field(..., description="Rule code, e.g. RAPID_ONWARD_TRANSFER")
    title: str = Field(..., description="Human-readable alert title")
    priority: str = Field(..., description="Severity priority: CRITICAL, HIGH, MEDIUM, LOW")
    score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Replaceable risk/priority score (scoring pending Aryan formula)",
    )
    account_ids: list[str] = Field(
        default_factory=list,
        description="Chronological/topological list of involved account IDs",
    )
    vpas: list[str] = Field(
        default_factory=list,
        description="Chronological/topological list of involved VPAs",
    )
    txn_ids: list[str] = Field(
        default_factory=list,
        description="Chronological list of participating transaction IDs",
    )
    evidence: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured quantitative evidence and hop breakdown",
    )
    explanation: str = Field(..., description="Explainable narrative of detected pattern")
    limitations: list[str] = Field(
        default_factory=list,
        description="Caveats and investigative decision-support reminders",
    )
    alternative_explanations: list[str] = Field(
        default_factory=list,
        description="Plausible non-fraud business or personal explanations",
    )
    complaint_ids: list[str] = Field(
        default_factory=list,
        description="Associated victim complaint IDs if present",
    )
    related_alert_ids: list[str] = Field(
        default_factory=list,
        description="Related alert IDs within the same investigation context",
    )
    ring_id: Optional[str] = Field(
        default=None,
        description="Linked fraud ring ID if clustered into a wider ring",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the alert was generated",
    )
    graph_context: Optional[dict[str, Any]] = Field(
        default=None,
        description="Optional lightweight subgraph nodes and edges for visual rendering",
    )

    @field_validator("created_at", mode="before")
    @classmethod
    def validate_alert_created_at(cls, v: Any) -> datetime:
        """Ensure created_at is a valid timezone-aware UTC datetime."""
        if isinstance(v, datetime):
            if v.tzinfo is None:
                return v.replace(tzinfo=timezone.utc)
            return v.astimezone(timezone.utc)
        if isinstance(v, str):
            dt = datetime.fromisoformat(v)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        return datetime.now(timezone.utc)
