"""Turso database connection and connectivity check utilities."""

from typing import Optional

import turso_serverless

from app.core.config import settings


def get_turso_connection(
    url: Optional[str] = None,
    auth_token: Optional[str] = None,
) -> turso_serverless.Connection:
    """Obtain a remote connection to Turso database using turso_serverless.

    Args:
        url: Optional database URL. Falls back to settings.TURSO_DATABASE_URL.
        auth_token: Optional auth token. Falls back to settings.TURSO_AUTH_TOKEN.

    Returns:
        turso_serverless.Connection: Open database connection.

    Raises:
        ValueError: If TURSO_DATABASE_URL is not configured or empty.
    """
    target_url = url if url is not None else settings.TURSO_DATABASE_URL
    if not target_url or not target_url.strip():
        raise ValueError("TURSO_DATABASE_URL is not configured")

    target_auth_token = auth_token if auth_token is not None else settings.TURSO_AUTH_TOKEN
    return turso_serverless.connect(target_url.strip(), auth_token=target_auth_token)


def _sanitize_error_message(message: str, auth_token: Optional[str] = None) -> str:
    """Mask any sensitive tokens from error messages."""
    sanitized = message
    tokens_to_mask: list[str] = []
    if auth_token and auth_token.strip():
        tokens_to_mask.append(auth_token.strip())
    if settings.TURSO_AUTH_TOKEN and settings.TURSO_AUTH_TOKEN.strip():
        tokens_to_mask.append(settings.TURSO_AUTH_TOKEN.strip())

    for token in tokens_to_mask:
        sanitized = sanitized.replace(token, "***")

    return sanitized


def check_connection(
    url: Optional[str] = None,
    auth_token: Optional[str] = None,
) -> tuple[bool, str]:
    """Test Turso database connectivity by executing SELECT 1.

    Args:
        url: Optional database URL. Falls back to settings.TURSO_DATABASE_URL.
        auth_token: Optional auth token. Falls back to settings.TURSO_AUTH_TOKEN.

    Returns:
        tuple[bool, str]: (True, "Database connection successful") on success,
                          (False, "TURSO_DATABASE_URL is not configured") if unconfigured,
                          (False, "Connection failed: <message>") on failure.
    """
    conn = None
    cursor = None
    try:
        conn = get_turso_connection(url=url, auth_token=auth_token)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        return (True, "Database connection successful")
    except ValueError as e:
        if "TURSO_DATABASE_URL is not configured" in str(e):
            return (False, "TURSO_DATABASE_URL is not configured")
        safe_msg = _sanitize_error_message(str(e), auth_token=auth_token)
        return (False, f"Connection failed: {safe_msg}")
    except Exception as e:
        safe_msg = _sanitize_error_message(str(e), auth_token=auth_token)
        return (False, f"Connection failed: {safe_msg}")
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
