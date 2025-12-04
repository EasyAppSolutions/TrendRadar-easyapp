"""Database module for TrendRadar PostgreSQL integration."""

from .connection import get_db_connection, DATABASE_URL, test_connection
from .repository import (
    get_or_create_source,
    upsert_headline,
    get_today_headlines,
    get_new_headlines_since,
    save_crawl_session,
    record_push,
    sync_word_groups_to_db,
)

__all__ = [
    "get_db_connection",
    "DATABASE_URL",
    "test_connection",
    "get_or_create_source",
    "upsert_headline",
    "get_today_headlines",
    "get_new_headlines_since",
    "save_crawl_session",
    "record_push",
    "sync_word_groups_to_db",
]
