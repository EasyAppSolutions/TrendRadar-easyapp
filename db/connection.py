"""PostgreSQL connection handling for TrendRadar."""

import os
from contextlib import contextmanager
from typing import Generator

import psycopg2
from psycopg2.extras import RealDictCursor


# Priority: DB_CONNECTION_STRING > DATABASE_URL > default
DATABASE_URL = os.getenv(
    "DB_CONNECTION_STRING",
    os.getenv(
        "DATABASE_URL",
        "postgresql://trendradar:changeme@localhost:5432/trendradar"
    )
)


@contextmanager
def get_db_connection() -> Generator:
    """Get a database connection with automatic commit/rollback.

    Usage:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM sources")
                rows = cur.fetchall()

    Yields:
        psycopg2 connection with RealDictCursor
    """
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def test_connection() -> bool:
    """Test database connectivity.

    Returns:
        True if connection successful, False otherwise
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False
