"""Readiness check endpoint distinguishing service liveness from database readiness."""

from fastapi import APIRouter, Response, status
from pydantic import BaseModel

from app.core.config import settings
from app.db.turso import check_connection

router = APIRouter()


class DatabaseStatus(BaseModel):
    connected: bool
    message: str


class ReadinessResponse(BaseModel):
    status: str
    database: DatabaseStatus
    environment: str


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    responses={
        200: {"description": "Service is ready and database is connected"},
        503: {"description": "Service is not ready - database connectivity check failed"},
    },
)
def check_readiness(response: Response) -> ReadinessResponse:
    """Check readiness of backend service and its backing database."""
    is_connected, message = check_connection()

    if not is_connected:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return ReadinessResponse(
            status="not_ready",
            database=DatabaseStatus(connected=False, message=message),
            environment=settings.ENVIRONMENT,
        )

    return ReadinessResponse(
        status="ready",
        database=DatabaseStatus(connected=True, message=message),
        environment=settings.ENVIRONMENT,
    )
