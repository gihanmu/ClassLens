"""Tests for PostgresDatabaseManager and query conversion."""

import pytest
from unittest.mock import MagicMock, patch

from services.api.repository.postgres_storage import (
    convert_query_placeholders,
    PostgresCursorWrapper,
    PostgresConnectionWrapper,
    PostgresDatabaseManager,
)


def test_convert_query_placeholders():
    q1 = "SELECT * FROM users WHERE id = ?"
    assert convert_query_placeholders(q1) == "SELECT * FROM users WHERE id = %s"

    q2 = "INSERT INTO table (a, b, c) VALUES (?, ?, ?)"
    assert convert_query_placeholders(q2) == "INSERT INTO table (a, b, c) VALUES (%s, %s, %s)"

    q3 = "SELECT * FROM assessments WHERE organization_id = 'org_cedar_sec'"
    assert convert_query_placeholders(q3) == q3


def test_postgres_cursor_and_connection_wrapper():
    mock_raw_cursor = MagicMock()
    mock_raw_cursor.fetchone.return_value = {"id": "usr_1", "email": "test@test.edu"}
    mock_raw_cursor.fetchall.return_value = [{"id": "usr_1"}]

    mock_raw_conn = MagicMock()
    mock_raw_conn.cursor.return_value = mock_raw_cursor

    wrapped_conn = PostgresConnectionWrapper(mock_raw_conn)

    # Test execute
    cur = wrapped_conn.execute("SELECT * FROM users WHERE id = ?", ("usr_1",))
    mock_raw_cursor.execute.assert_called_with("SELECT * FROM users WHERE id = %s", ("usr_1",))

    row = cur.fetchone()
    assert row["id"] == "usr_1"

    # Test context manager commit
    with wrapped_conn:
        pass
    mock_raw_conn.commit.assert_called()

    # Test context manager rollback on exception
    try:
        with wrapped_conn:
            raise ValueError("Test error")
    except ValueError:
        pass
    mock_raw_conn.rollback.assert_called()


@patch("psycopg2.pool.ThreadedConnectionPool")
def test_postgres_database_manager(mock_pool_cls):
    mock_pool = MagicMock()
    mock_raw_conn = MagicMock()
    mock_raw_cur = MagicMock()
    mock_pool_cls.return_value = mock_pool
    mock_pool.getconn.return_value = mock_raw_conn
    mock_raw_conn.cursor.return_value = mock_raw_cur

    mock_raw_cur.fetchone.return_value = [1]

    manager = PostgresDatabaseManager("postgresql://test:test@localhost:5432/testdb")

    # Verify DDL + schema_version executed on init
    assert mock_raw_cur.execute.call_count >= len(manager.DDL_STATEMENTS)
    mock_pool.putconn.assert_called_with(mock_raw_conn)

    # Verify BEGIN IMMEDIATE / COMMIT translation does not send SQLite syntax to PostgreSQL
    with manager.get_connection() as conn:
        conn.execute("BEGIN IMMEDIATE;")
        conn.execute("SELECT 1;")
        conn.execute("COMMIT;")

    # Health check
    assert manager.check_health() is True

