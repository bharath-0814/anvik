import json
from pathlib import Path
from typing import Any, Generator, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.schemas.complaints import ComplaintItem, ComplaintsResponse
from app.db.turso import get_turso_connection

router = APIRouter(tags=["Complaints"])

ALERTS_DATA_PATH = Path(__file__).resolve().parent.parent.parent / "detection" / "alerts_data.json"


def get_db() -> Generator[Any, None, None]:
    """Provide a database connection context and guarantee cleanup."""
    try:
        conn = get_turso_connection()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection unavailable: {exc}",
        ) from exc
    try:
        yield conn
    finally:
        try:
            conn.close()
        except Exception:
            pass


@router.get(
    "/complaints",
    response_model=ComplaintsResponse,
    summary="Get preloaded synthetic complaints",
    description=(
        "Returns preloaded synthetic complaints with joined transaction "
        "amounts and beneficiary details."
    ),
)
def get_complaints(
    account_id: Optional[str] = Query(
        None,
        description="Filter complaints by complainant victim account ID",
    ),
    conn: Any = Depends(get_db),
) -> ComplaintsResponse:
    """Retrieve preloaded synthetic complaints from database."""
    try:
        cur = conn.cursor()
        query = (
            "SELECT "
            "  c.complaint_id, "
            "  c.victim_account_id, "
            "  c.victim_vpa, "
            "  c.txn_id, "
            "  t.amount_inr, "
            "  t.receiver_account_id, "
            "  t.receiver_vpa, "
            "  COALESCE(c.complaint_date_utc, c.raw_complaint_date) as complaint_date, "
            "  t.device_id "
            "FROM complaints c "
            "LEFT JOIN transactions t ON c.txn_id = t.txn_id "
        )
        params: list[Any] = []
        if account_id:
            query += "WHERE c.victim_account_id = ? "
            params.append(account_id)

        query += "ORDER BY c.complaint_id ASC"

        if params:
            cur.execute(query, tuple(params))
        else:
            cur.execute(query)

        rows = cur.fetchall()

        # Load alerts data from realscore engine output if available
        alerts: list[dict[str, Any]] = []
        if ALERTS_DATA_PATH.exists():
            try:
                with open(ALERTS_DATA_PATH, "r", encoding="utf-8") as f:
                    raw_alerts_data = json.load(f)
                    alerts = raw_alerts_data.get("alerts", [])
            except Exception:
                alerts = []

        complaints: list[ComplaintItem] = []
        for r in rows:
            cid = r[0]
            v_acc = r[1]
            v_vpa = r[2]
            txn_id = r[3]
            amt = r[4]
            rec_acc = r[5]
            rec_vpa = r[6]
            c_date = r[7]
            dev_id = r[8] if len(r) > 8 else None

            # Calculate dynamic risk score and triage priority from realscore engine alerts
            matching = [
                a for a in alerts
                if cid in a.get("complaint_ids", [])
                or txn_id in a.get("txn_ids", [])
                or txn_id in a.get("linked_txn_ids", [])
                or (rec_acc and rec_acc in a.get("account_ids", []))
            ]

            if matching:
                best_alert = max(matching, key=lambda a: float(a.get("score", 0.0)))
                calculated_score = int(round(float(best_alert.get("score", 0.0)) * 100))
                priority = best_alert.get("priority", "low").upper()
                rule_triggers = sorted(list(set(a.get("rule_id") for a in matching if a.get("rule_id"))))
            else:
                calculated_score = 20
                priority = "LOW"
                rule_triggers = []

            if calculated_score >= 75:
                triage_status = "Open"
            elif calculated_score >= 45:
                triage_status = "In review"
            else:
                triage_status = "Resolved"

            complaints.append(
                ComplaintItem(
                    complaint_id=cid,
                    victim_account_id=v_acc,
                    victim_vpa=v_vpa,
                    txn_id=txn_id,
                    amount_inr=amt,
                    beneficiary_account_id=rec_acc,
                    beneficiary_vpa=rec_vpa,
                    complaint_date=c_date,
                    status="UNDER_INVESTIGATION",
                    device_id=dev_id,
                    risk_score=calculated_score,
                    priority=priority,
                    triage_status=triage_status,
                    rule_triggers=rule_triggers,
                )
            )

        return ComplaintsResponse(
            total_count=len(complaints),
            complaints=complaints,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch complaints: {exc}",
        ) from exc
