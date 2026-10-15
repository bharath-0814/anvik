"""API routes for read-only preloaded synthetic complaints."""

from typing import Any, Generator, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.schemas.complaints import ComplaintItem, ComplaintsResponse
from app.db.turso import get_turso_connection

router = APIRouter(tags=["Complaints"])


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
            "  COALESCE(c.complaint_date_utc, c.raw_complaint_date) as complaint_date "
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
        complaints: list[ComplaintItem] = []
        for r in rows:
            complaints.append(
                ComplaintItem(
                    complaint_id=r[0],
                    victim_account_id=r[1],
                    victim_vpa=r[2],
                    txn_id=r[3],
                    amount_inr=r[4],
                    beneficiary_account_id=r[5],
                    beneficiary_vpa=r[6],
                    complaint_date=r[7],
                    status="UNDER_INVESTIGATION",
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
