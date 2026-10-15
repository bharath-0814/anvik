"""Versioned SQL migration runner for Turso and SQLite databases."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.db.turso import get_turso_connection

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent.parent / "migrations"


def ensure_migration_table(conn: Any) -> None:
    """Ensure the schema_migrations tracking table exists."""
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at_utc TEXT NOT NULL
        );
        """
    )
    cursor.close()


def get_applied_migrations(conn: Any) -> set[str]:
    """Retrieve the set of already applied migration versions."""
    ensure_migration_table(conn)
    cursor = conn.cursor()
    cursor.execute("SELECT version FROM schema_migrations ORDER BY version;")
    rows = cursor.fetchall()
    cursor.close()
    return {r[0] for r in rows}


def run_migrations(conn: Any = None, migrations_dir: Path = MIGRATIONS_DIR) -> list[str]:
    """Apply any pending SQL migrations in sorted order.

    Args:
        conn: Optional DB-API connection. If None, uses get_turso_connection().
        migrations_dir: Directory containing .sql migration files.

    Returns:
        list[str]: Versions of newly applied migrations.
    """
    should_close = False
    if conn is None:
        conn = get_turso_connection()
        should_close = True

    applied_now: list[str] = []
    try:
        ensure_migration_table(conn)
        applied_versions = get_applied_migrations(conn)

        if not migrations_dir.exists():
            return applied_now

        migration_files = sorted(migrations_dir.glob("*.sql"))
        for sql_file in migration_files:
            version = sql_file.stem.split("_")[0]
            name = sql_file.stem

            if version in applied_versions:
                continue

            with open(sql_file, "r", encoding="utf-8") as f:
                sql_content = f.read()

            # Execute SQL statements
            cursor = conn.cursor()
            # Split by semicolon to execute individually across DB-API drivers
            statements = [s.strip() for s in sql_content.split(";") if s.strip()]
            for stmt in statements:
                cursor.execute(stmt)

            now_utc = datetime.now(timezone.utc).isoformat()
            cursor.execute(
                "INSERT INTO schema_migrations (version, name, applied_at_utc) VALUES (?, ?, ?);",
                (version, name, now_utc),
            )
            cursor.close()
            applied_now.append(version)

        return applied_now
    finally:
        if should_close and conn is not None:
            conn.close()
