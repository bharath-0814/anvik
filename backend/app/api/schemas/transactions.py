"""Pydantic schemas for transactions API."""

from typing import Optional

from pydantic import BaseModel, Field


class TransactionResponse(BaseModel):
    """Pydantic response model for a single transaction record."""

    txn_id: str = Field(..., description="Unique transaction ID")
    sender_account_id: str = Field(..., description="Account ID of the sender")
    receiver_account_id: str = Field(..., description="Account ID of the receiver")
    sender_vpa: str = Field(..., description="Sender VPA handle")
    receiver_vpa: str = Field(..., description="Receiver VPA handle")
    amount_paise: int = Field(..., description="Transaction amount in paise")
    amount_inr: float = Field(..., description="Transaction amount in INR")
    raw_timestamp: str = Field(..., description="Raw recorded timestamp")
    timestamp_utc: str = Field(..., description="Normalized UTC timestamp")
    txn_type: str = Field(..., description="Type of transaction, e.g. PAY")
    status: str = Field(..., description="Transaction status, e.g. SUCCESS")
    device_id: Optional[str] = Field(None, description="Device ID used for the transaction")
