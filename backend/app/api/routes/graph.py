"""Graph API endpoints for Cytoscape.js visualization."""

from typing import Any, Generator, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.schemas.graph import GraphResponse
from app.db.turso import get_turso_connection
from app.services.graph_service import get_graph_data

router = APIRouter(tags=["Graph"])


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
    "/graph",
    response_model=GraphResponse,
    summary="Get transaction and device interaction graph",
    description=(
        "Returns Cytoscape.js compatible nodes and edges representing synthetic "
        "accounts, devices, and transactions."
    ),
)
def get_graph(
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        description="Filter transactions by status (e.g. SUCCESS, FAILED)",
    ),
    limit: Optional[int] = Query(
        None,
        ge=1,
        description="Limit the number of transactions to include in the graph",
    ),
    conn: Any = Depends(get_db),
) -> GraphResponse:
    """Retrieve full or filtered Cytoscape graph."""
    try:
        return get_graph_data(conn=conn, status=status_filter, limit=limit)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate graph: {exc}",
        ) from exc
