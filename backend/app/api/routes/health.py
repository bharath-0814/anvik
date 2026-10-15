"""Health check route for Anvik Backend."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def get_health() -> dict[str, str]:
    """Return health status of the service independent of external dependencies."""
    return {"status": "healthy", "service": "anvik-backend"}
