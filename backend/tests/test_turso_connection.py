"""Unit tests for Turso database connectivity and configuration."""

from unittest.mock import MagicMock, patch

import pytest
from app.core.config import Settings, settings
from app.db.turso import check_connection, get_turso_connection
from scripts.check_turso_connection import main as cli_main


def test_successful_connection_executing_select_1() -> None:
    """Test 1: Verify successful connection and execution of SELECT 1."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    with patch("turso_serverless.connect", return_value=mock_conn) as mock_connect:
        success, message = check_connection(
            url="libsql://test-db.turso.io",
            auth_token="dummy-test-token",
        )

        assert success is True
        assert message == "Database connection successful"
        mock_connect.assert_called_once_with(
            "libsql://test-db.turso.io",
            auth_token="dummy-test-token",
        )
        mock_conn.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once_with("SELECT 1")
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()


def test_connection_failure_handling_driver_exception() -> None:
    """Test 2: Verify safe handling when the driver throws a connection or execution exception."""
    secret_token = "secret-token-super-confidential"
    with patch(
        "turso_serverless.connect",
        side_effect=Exception(f"Connection failed to remote host with token {secret_token}"),
    ):
        success, message = check_connection(
            url="libsql://test-db.turso.io",
            auth_token=secret_token,
        )

        assert success is False
        assert message.startswith("Connection failed:")
        assert secret_token not in message
        assert "***" in message

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.execute.side_effect = Exception("Query execution error")

    with patch("turso_serverless.connect", return_value=mock_conn):
        success, message = check_connection(
            url="libsql://test-db.turso.io",
            auth_token="test-token",
        )

        assert success is False
        assert "Query execution error" in message
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()


def test_unconfigured_missing_credentials_safe_failure() -> None:
    """Test 3: Unconfigured or missing credentials returns safe failure without network call."""
    with patch("turso_serverless.connect") as mock_connect:
        with patch.object(settings, "TURSO_DATABASE_URL", None):
            success, message = check_connection(url=None)
            assert success is False
            assert message == "TURSO_DATABASE_URL is not configured"
            mock_connect.assert_not_called()

        with patch.object(settings, "TURSO_DATABASE_URL", "   "):
            success, message = check_connection(url=None)
            assert success is False
            assert message == "TURSO_DATABASE_URL is not configured"
            mock_connect.assert_not_called()


def test_get_turso_connection_raises_value_error_when_missing() -> None:
    """Verify get_turso_connection directly raises ValueError when URL is not configured."""
    with patch.object(settings, "TURSO_DATABASE_URL", None):
        with pytest.raises(ValueError, match="TURSO_DATABASE_URL is not configured"):
            get_turso_connection(url="")

        with pytest.raises(ValueError, match="TURSO_DATABASE_URL is not configured"):
            get_turso_connection(url=None)


def test_settings_masks_auth_token_representation() -> None:
    """Verify that settings repr and str do not leak TURSO_AUTH_TOKEN."""
    s = Settings(
        TURSO_DATABASE_URL="libsql://example.turso.io",
        TURSO_AUTH_TOKEN="super-secret-auth-key",
    )
    assert "super-secret-auth-key" not in repr(s)
    assert "super-secret-auth-key" not in str(s)
    assert "***" in repr(s)


def test_cli_script_main_success_and_failure() -> None:
    """Verify CLI check_turso_connection main exits 0 on success and 1 on failure."""
    with patch("scripts.check_turso_connection.check_connection", return_value=(True, "Success")):
        exit_code = cli_main()
        assert exit_code == 0

    with patch("scripts.check_turso_connection.check_connection", return_value=(False, "Failed")):
        exit_code = cli_main()
        assert exit_code == 1
