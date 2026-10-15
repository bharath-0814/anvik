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
    redirect_slashes=False,
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

@app.get("/", summary="Root status check")
@app.get("/api/index.py", summary="Serverless entrypoint fallback")
@app.get("/api/index", summary="Serverless entrypoint fallback")
def root_check():
    """Service liveness indicator at root."""
    return {"status": "healthy", "service": "anvik-backend"}

# Mount with /api prefix
app.include_router(health_router, prefix="/api")
app.include_router(ready_router, prefix="/api")
app.include_router(graph_router, prefix="/api")
app.include_router(complaints_router, prefix="/api")
app.include_router(alerts_router, prefix="/api")

# Also mount without /api prefix for routing flexibility under serverless rewrites
app.include_router(health_router)
app.include_router(ready_router)
app.include_router(graph_router)
app.include_router(complaints_router)
app.include_router(alerts_router)
