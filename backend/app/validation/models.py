"""Pydantic models and parser utilities for Anvik source datasets and contracts."""

from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Optional
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, field_validator, model_validator

IST = ZoneInfo("Asia/Kolkata")


def parse_ist_timestamp(ts_input: Any) -> tuple[datetime, str]:
    """Parse a timestamp string.

    If naive, interpret as IST (Asia/Kolkata) and convert to UTC.
    If already aware (e.g. ending in Z or containing offset), convert to UTC directly.

    Returns:
        tuple[datetime, str]: (aware_utc_datetime, original_string_representation)
    """
    orig_str = str(ts_input).strip()
    try:
        # Standard ISO or space-separated format (e.g. '2026-09-03 00:18:50')
        dt = datetime.fromisoformat(orig_str.replace("Z", "+00:00"))
    except ValueError as e:
        # Fallback to strptime if needed
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(orig_str, fmt)
                break
            except ValueError:
                continue
        else:
            raise ValueError(f"Invalid timestamp format: {orig_str}") from e

    if dt.tzinfo is None:
        # Naive: interpret as IST, then convert to UTC
        aware_ist = dt.replace(tzinfo=IST)
        aware_utc = aware_ist.astimezone(timezone.utc)
    else:
        # Already has timezone info: convert to UTC
        aware_utc = dt.astimezone(timezone.utc)

    return aware_utc, orig_str


def parse_utc_timestamp(ts_input: Any) -> datetime:
    """Parse an explicitly UTC timestamp (such as those from alert bundles)."""
    orig_str = str(ts_input).strip()
    dt = datetime.fromisoformat(orig_str.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError(f"Alert bundle timestamp must be explicitly timezone-aware: {orig_str}")
    return dt.astimezone(timezone.utc)


def parse_inr_amount(amount_input: Any) -> tuple[Decimal, int]:
    """Parse an INR currency amount decimal-safely.

    Returns:
        tuple[Decimal, int]: (decimal_inr_amount, integer_paise)

    Raises:
        ValueError: If amount is negative, zero, invalid, or has more than 2 decimal places.
    """
    try:
        val = Decimal(str(amount_input).strip())
    except (InvalidOperation, ValueError) as e:
        raise ValueError(f"Invalid numeric amount: {amount_input}") from e

    if val <= 0:
        raise ValueError(f"Amount must be positive: {val}")

    # Check decimal places (cannot exceed 2 decimal places)
    exp = val.as_tuple().exponent
    if isinstance(exp, int) and exp < -2:
        raise ValueError(f"Amount has more than two decimal places: {val}")

    # Convert to integer paise (1 INR = 100 paise)
    paise = int(round(val * 100))
    return val, paise


class AccountRecord(BaseModel):
    """Raw account entity from accounts.csv."""

    account_id: str = Field(..., min_length=1)
    holder_name: str = Field(..., min_length=1)
    vpa: str = Field(..., min_length=1)
    bank: str = Field(..., min_length=1)
    created_at: date


class DeviceRecord(BaseModel):
    """Account to device mapping from devices.csv."""

    device_id: str = Field(..., min_length=1)
    account_id: str = Field(..., min_length=1)


class ComplaintRecord(BaseModel):
    """Formal dispute/complaint record from complaints.csv."""

    complaint_id: str = Field(..., min_length=1)
    victim_vpa: str = Field(..., min_length=1)
    txn_id: str = Field(..., min_length=1)
    complaint_date: date


class TransactionRecord(BaseModel):
    """Transaction record with normalized UTC timestamp and decimal-safe INR amount."""

    txn_id: str = Field(..., min_length=1)
    raw_timestamp: str
    timestamp_utc: datetime
    sender_vpa: str = Field(..., min_length=1)
    receiver_vpa: str = Field(..., min_length=1)
    amount: Decimal
    amount_paise: int
    txn_type: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    device_id: str = Field(..., min_length=1)

    @classmethod
    def from_raw(
        cls,
        txn_id: str,
        timestamp: str,
        sender_vpa: str,
        receiver_vpa: str,
        amount: Any,
        txn_type: str,
        status: str,
        device_id: str,
    ) -> "TransactionRecord":
        utc_dt, raw_ts = parse_ist_timestamp(timestamp)
        dec_amt, paise = parse_inr_amount(amount)
        return cls(
            txn_id=str(txn_id).strip(),
            raw_timestamp=raw_ts,
            timestamp_utc=utc_dt,
            sender_vpa=str(sender_vpa).strip(),
            receiver_vpa=str(receiver_vpa).strip(),
            amount=dec_amt,
            amount_paise=paise,
            txn_type=str(txn_type).strip(),
            status=str(status).strip(),
            device_id=str(device_id).strip(),
        )


class ExpectedScenario(BaseModel):
    """Ground truth test scenario from expected_results.json."""

    scenario_id: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    should_alert: bool
    expected_rules: list[str] = Field(default_factory=list)
    accounts: list[str] = Field(default_factory=list)
    txn_ids: list[str] = Field(default_factory=list)
    complaint_ids: list[str] = Field(default_factory=list)
    devices: list[str] = Field(default_factory=list)
    note: Optional[str] = None


class AlertRecord(BaseModel):
    """Alert record schema matching Aryan's proposed alert bundle."""

    alert_id: str = Field(..., min_length=1)
    rule_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    priority: str = Field(..., min_length=1)
    score: float = Field(..., ge=0.0, le=100.0)
    created_at: datetime
    account_ids: list[str] = Field(default_factory=list)
    vpas: list[str] = Field(default_factory=list)
    txn_ids: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)
    explanation: str = Field(..., min_length=1)
    limitations: list[str] = Field(default_factory=list)
    alternative_explanations: list[str] = Field(default_factory=list)
    complaint_ids: list[str] = Field(default_factory=list)
    related_alert_ids: list[str] = Field(default_factory=list)
    ring_id: Optional[str] = None

    @field_validator("created_at", mode="before")
    @classmethod
    def validate_alert_created_at(cls, v: Any) -> datetime:
        if isinstance(v, datetime):
            if v.tzinfo is None:
                raise ValueError("created_at must be timezone-aware (UTC)")
            return v.astimezone(timezone.utc)
        return parse_utc_timestamp(v)


class RingRecord(BaseModel):
    """Fraud ring grouping in alert bundle."""

    ring_id: str = Field(..., min_length=1)
    alert_ids: list[str] = Field(default_factory=list)
    account_ids: list[str] = Field(default_factory=list)
    pattern_type: Optional[str] = None


class AccountSummary(BaseModel):
    """Account summary record in alert bundle."""

    account_id: str = Field(..., min_length=1)
    vpa: Optional[str] = None
    role: Optional[str] = None
    total_sent_inr: Optional[float] = None
    total_received_inr: Optional[float] = None


class AlertBundle(BaseModel):
    """Full alert bundle contract from Aryan."""

    dataset_id: str = Field(..., min_length=1)
    generated_at: datetime
    amount_unit: str = "INR"
    count: int = Field(..., ge=0)
    alerts: list[AlertRecord] = Field(default_factory=list)
    rings: list[RingRecord] = Field(default_factory=list)
    account_summaries: list[AccountSummary] = Field(default_factory=list)

    @field_validator("generated_at", mode="before")
    @classmethod
    def validate_bundle_generated_at(cls, v: Any) -> datetime:
        if isinstance(v, datetime):
            if v.tzinfo is None:
                raise ValueError("generated_at must be timezone-aware (UTC)")
            return v.astimezone(timezone.utc)
        return parse_utc_timestamp(v)

    @model_validator(mode="after")
    def validate_bundle_integrity(self) -> "AlertBundle":
        if self.count != len(self.alerts):
            raise ValueError(
                f"Bundle count ({self.count}) does not match alerts length ({len(self.alerts)})"
            )

        # Alert IDs unique
        alert_ids = [a.alert_id for a in self.alerts]
        if len(alert_ids) != len(set(alert_ids)):
            duplicates = [aid for aid in alert_ids if alert_ids.count(aid) > 1]
            raise ValueError(f"Duplicate alert_id(s) detected in bundle: {set(duplicates)}")

        # Ring IDs unique
        ring_ids = [r.ring_id for r in self.rings]
        if len(ring_ids) != len(set(ring_ids)):
            duplicates = [rid for rid in ring_ids if ring_ids.count(rid) > 1]
            raise ValueError(f"Duplicate ring_id(s) detected in bundle: {set(duplicates)}")

        # Validate ring references
        known_alert_ids = set(alert_ids)
        known_ring_ids = set(ring_ids)
        for ring in self.rings:
            for aid in ring.alert_ids:
                if aid not in known_alert_ids:
                    raise ValueError(f"Ring '{ring.ring_id}' references unknown alert_id '{aid}'")

        for alert in self.alerts:
            if alert.ring_id and alert.ring_id not in known_ring_ids:
                raise ValueError(
                    f"Alert '{alert.alert_id}' references unknown ring_id '{alert.ring_id}'"
                )
            for rel_id in alert.related_alert_ids:
                if rel_id not in known_alert_ids:
                    raise ValueError(
                        f"Alert '{alert.alert_id}' references unknown related_alert_id '{rel_id}'"
                    )

        return self
