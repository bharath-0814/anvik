"""Vercel Serverless Function entrypoint for Anvik FastAPI Backend."""

import sys
from pathlib import Path

# Add backend directory to sys.path so 'app' and 'detection' packages resolve
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402

# Export for ASGI
app = app
