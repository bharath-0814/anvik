"""Main FastAPI application entrypoint for Anvik Backend."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.alerts import router as alerts_router
from app.api.routes.complaints import router as complaints_router
from app.api.routes.graph import router as graph_router
from app.api.routes.health import router as health_router
from app.api.routes.ready import router as ready_router

app = FastAPI(
    title="Anvik Backend API",
    version="0.1.0",
    description="UPI Fraud-Ring Graph Investigator Backend",
)

# CORS Configuration allowing production Vercel frontend, local development, and preview deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://anvik-frontend-alpha.vercel.app",
        "https://avnikfrontend.vercel.app",
    ],
    allow_origin_regex=r"^https:\/\/.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(ready_router, prefix="/api")
app.include_router(graph_router, prefix="/api")
app.include_router(complaints_router, prefix="/api")
app.include_router(alerts_router, prefix="/api")
