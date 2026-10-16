"""Pydantic schemas for read-only complaints API."""

from typing import Optional

from pydantic import BaseModel, Field


class ComplaintItem(BaseModel):
    """Single preloaded synthetic complaint record."""

    complaint_id: str = Field(..., description="Unique complaint reference, e.g. CMP0001")
    victim_account_id: str = Field(..., description="Account ID of the complainant")
    victim_vpa: str = Field(..., description="VPA handle of the complainant")
    txn_id: str = Field(..., description="Disputed transaction ID")
    amount_inr: Optional[float] = Field(None, description="Disputed amount in INR")
    beneficiary_account_id: Optional[str] = Field(
        None, description="Account ID that received the funds"
    )
    beneficiary_vpa: Optional[str] = Field(
        None, description="VPA handle that received the funds"
    )
    complaint_date: str = Field(..., description="Recorded date of dispute filing")
    status: str = Field("UNDER_INVESTIGATION", description="Current complaint workflow status")
    device_id: Optional[str] = Field(None, description="Associated device identifier from transaction")
    risk_score: Optional[int] = Field(
        None, description="Dynamic risk score (0-100) calculated from realscore engine"
    )
    priority: Optional[str] = Field(None, description="Triage priority: HIGH, MEDIUM, LOW")
    triage_status: Optional[str] = Field(
        "Open", description="Investigation triage status: Open, In review, Resolved"
    )
    rule_triggers: Optional[list[str]] = Field(
        default_factory=list, description="Rules triggered in detection engine"
    )


class ComplaintsResponse(BaseModel):
    """List response for preloaded complaints."""

    total_count: int
    complaints: list[ComplaintItem]
