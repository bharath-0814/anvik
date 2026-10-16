"""API routes for transaction details."""

from typing import Any, Generator

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.schemas.transactions import TransactionResponse
from app.db.repository import get_transaction_by_id
from app.db.turso import get_turso_connection

router = APIRouter(tags=["Transactions"])


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
    "/transactions/{txn_id}",
    response_model=TransactionResponse,
    summary="Get transaction by ID",
    description="Fetch details of a single transaction by its unique identifier.",
)
def get_transaction(
    txn_id: str,
    conn: Any = Depends(get_db),
) -> TransactionResponse:
    """Retrieve transaction details by ID."""
    txn = get_transaction_by_id(conn, txn_id)
    if txn is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    return TransactionResponse(**txn)
