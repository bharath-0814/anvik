"""CLI script to verify Turso database connectivity."""

import sys
from pathlib import Path

# Ensure backend directory is in sys.path so app packages can be imported
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.config import Settings, settings  # noqa: E402
from app.db.turso import check_connection  # noqa: E402


def main() -> int:
    """Run Turso connection check and output status."""
    print("Checking Turso database connectivity...")

    active_settings = settings
    # If not loaded from CWD .env, check if backend/.env exists
    if not active_settings.TURSO_DATABASE_URL:
        backend_env = backend_dir / ".env"
        if backend_env.exists():
            active_settings = Settings(_env_file=str(backend_env))

    db_url = active_settings.TURSO_DATABASE_URL
    if db_url:
        print(f"Target Database URL: {db_url}")
    else:
        print("Target Database URL: <not configured>")

    success, message = check_connection(
        url=active_settings.TURSO_DATABASE_URL,
        auth_token=active_settings.TURSO_AUTH_TOKEN,
    )

    if success:
        print(f"[SUCCESS] {message}")
        return 0
    else:
        print(f"[FAILURE] {message}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
