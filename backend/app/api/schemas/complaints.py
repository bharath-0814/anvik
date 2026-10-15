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


class ComplaintsResponse(BaseModel):
    """List response for preloaded complaints."""

    total_count: int
    complaints: list[ComplaintItem]
