"""Main FastAPI application entrypoint for Anvik Backend."""

from fastapi import FastAPI

from app.api.routes.graph import router as graph_router
from app.api.routes.health import router as health_router
from app.api.routes.ready import router as ready_router

app = FastAPI(
    title="Anvik Backend API",
    version="0.1.0",
    description="UPI Fraud-Ring Graph Investigator Backend",
)

app.include_router(health_router, prefix="/api")
app.include_router(ready_router, prefix="/api")
app.include_router(graph_router, prefix="/api")
