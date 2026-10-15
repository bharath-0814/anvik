"""API routes for detection alerts and rings."""

import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.api.schemas.alerts import AlertsResponse

router = APIRouter(tags=["Alerts"])

ALERTS_DATA_PATH = Path(__file__).resolve().parent.parent.parent / "detection" / "alerts_data.json"


@router.get(
    "/alerts",
    response_model=AlertsResponse,
    summary="Get fraud detection alerts and rings",
    description=(
        "Returns explainable fraud-pattern alerts and ring clusters complying with "
        "Aryan's scoring v2.0 contract."
    ),
)
def get_alerts(
    rule_id: Optional[str] = Query(None, description="Filter alerts by rule ID"),
    priority: Optional[str] = Query(
        None, description="Filter alerts by priority ('high', 'medium', 'low')"
    ),
    account_id: Optional[str] = Query(None, description="Filter alerts involving this account ID"),
    txn_id: Optional[str] = Query(None, description="Filter alerts involving this transaction ID"),
) -> AlertsResponse:
    """Retrieve fraud-pattern alerts and ring clusters."""
    if not ALERTS_DATA_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerts data not found. Detection engine must be executed on dataset first.",
        )

    try:
        with open(ALERTS_DATA_PATH, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        alerts = raw_data.get("alerts", [])
        if rule_id:
            alerts = [a for a in alerts if a.get("rule_id", "").upper() == rule_id.upper()]
        if priority:
            alerts = [a for a in alerts if a.get("priority", "").lower() == priority.lower()]
        if account_id:
            alerts = [a for a in alerts if account_id in a.get("account_ids", [])]
        if txn_id:
            alerts = [
                a for a in alerts
                if txn_id in a.get("txn_ids", []) or txn_id in a.get("linked_txn_ids", [])
            ]

        response_data = dict(raw_data)
        response_data["alerts"] = alerts
        response_data["count"] = len(alerts)

        return AlertsResponse.model_validate(response_data)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load alerts: {exc}",
        ) from exc
