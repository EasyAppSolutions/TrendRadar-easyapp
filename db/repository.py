"""Database repository with CRUD operations for TrendRadar."""

from datetime import datetime
from typing import Dict, List, Optional, Tuple

from .connection import get_db_connection


# ============================================================================
# Source Operations
# ============================================================================

def get_or_create_source(conn, platform_id: str, platform_name: str) -> int:
    """Get or create a source by platform_id.

    Args:
        conn: Database connection
        platform_id: Platform identifier (e.g., 'toutiao', 'baidu')
        platform_name: Display name (e.g., '今日头条', '百度热搜')

    Returns:
        Source ID
    """
    with conn.cursor() as cur:
        # Try to get existing source
        cur.execute(
            "SELECT id FROM sources WHERE platform_id = %s",
            (platform_id,)
        )
        row = cur.fetchone()
        if row:
            return row['id']

        # Create new source
        cur.execute(
            """
            INSERT INTO sources (platform_id, platform_name)
            VALUES (%s, %s)
            RETURNING id
            """,
            (platform_id, platform_name)
        )
        return cur.fetchone()['id']


def get_all_sources(conn) -> List[Dict]:
    """Get all active sources.

    Returns:
        List of source dictionaries
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, platform_id, platform_name FROM sources WHERE is_active = true"
        )
        return cur.fetchall()


# ============================================================================
# Headline Operations
# ============================================================================

def upsert_headline(
    conn,
    source_id: int,
    title: str,
    url: str,
    mobile_url: str,
    rank: int,
    crawled_at: datetime
) -> int:
    """Insert or update a headline and record its occurrence.

    Args:
        conn: Database connection
        source_id: Source ID from sources table
        title: Headline text
        url: Desktop URL
        mobile_url: Mobile URL
        rank: Position in the list
        crawled_at: Timestamp of crawl

    Returns:
        Headline ID
    """
    with conn.cursor() as cur:
        # Upsert headline
        cur.execute(
            """
            INSERT INTO headlines (source_id, title, url, mobile_url, first_seen_at, last_seen_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (source_id, title) DO UPDATE SET
                url = EXCLUDED.url,
                mobile_url = EXCLUDED.mobile_url,
                last_seen_at = EXCLUDED.last_seen_at
            RETURNING id
            """,
            (source_id, title, url, mobile_url, crawled_at, crawled_at)
        )
        headline_id = cur.fetchone()['id']

        # Record occurrence
        cur.execute(
            """
            INSERT INTO headline_occurrences (headline_id, rank, crawled_at)
            VALUES (%s, %s, %s)
            """,
            (headline_id, rank, crawled_at)
        )

        return headline_id


def get_today_headlines(
    conn,
    platform_ids: List[str],
    today_start: datetime
) -> List[Dict]:
    """Get all headlines from today for given platforms.

    Args:
        conn: Database connection
        platform_ids: List of platform identifiers to filter
        today_start: Start of today (midnight)

    Returns:
        List of headline dictionaries with aggregated data
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                h.id,
                h.title,
                h.url,
                h.mobile_url,
                h.first_seen_at,
                h.last_seen_at,
                s.platform_id,
                s.platform_name,
                array_agg(DISTINCT ho.rank ORDER BY ho.rank) as ranks,
                count(ho.id) as occurrence_count
            FROM headlines h
            JOIN sources s ON h.source_id = s.id
            JOIN headline_occurrences ho ON h.id = ho.headline_id
            WHERE s.platform_id = ANY(%s)
              AND h.first_seen_at >= %s
            GROUP BY h.id, s.platform_id, s.platform_name
            ORDER BY h.last_seen_at DESC
            """,
            (platform_ids, today_start)
        )
        return cur.fetchall()


def get_new_headlines_since(
    conn,
    platform_ids: List[str],
    since: datetime
) -> List[Dict]:
    """Get headlines that first appeared after the given timestamp.

    Args:
        conn: Database connection
        platform_ids: List of platform identifiers
        since: Timestamp to compare against

    Returns:
        List of new headline dictionaries
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                h.id,
                h.title,
                h.url,
                h.mobile_url,
                h.first_seen_at,
                s.platform_id,
                s.platform_name,
                array_agg(DISTINCT ho.rank ORDER BY ho.rank) as ranks
            FROM headlines h
            JOIN sources s ON h.source_id = s.id
            JOIN headline_occurrences ho ON h.id = ho.headline_id
            WHERE s.platform_id = ANY(%s)
              AND h.first_seen_at >= %s
            GROUP BY h.id, s.platform_id, s.platform_name
            ORDER BY h.first_seen_at DESC
            """,
            (platform_ids, since)
        )
        return cur.fetchall()


def get_headlines_with_keyword(
    conn,
    keyword: str,
    today_start: datetime,
    platform_ids: Optional[List[str]] = None
) -> List[Dict]:
    """Get headlines containing a specific keyword.

    Args:
        conn: Database connection
        keyword: Keyword to search for
        today_start: Start of today
        platform_ids: Optional list of platforms to filter

    Returns:
        List of matching headline dictionaries
    """
    with conn.cursor() as cur:
        if platform_ids:
            cur.execute(
                """
                SELECT
                    h.id,
                    h.title,
                    h.url,
                    h.mobile_url,
                    h.first_seen_at,
                    h.last_seen_at,
                    s.platform_id,
                    s.platform_name,
                    array_agg(DISTINCT ho.rank ORDER BY ho.rank) as ranks,
                    count(ho.id) as occurrence_count
                FROM headlines h
                JOIN sources s ON h.source_id = s.id
                JOIN headline_occurrences ho ON h.id = ho.headline_id
                WHERE h.title ILIKE %s
                  AND s.platform_id = ANY(%s)
                  AND h.first_seen_at >= %s
                GROUP BY h.id, s.platform_id, s.platform_name
                ORDER BY occurrence_count DESC
                """,
                (f"%{keyword}%", platform_ids, today_start)
            )
        else:
            cur.execute(
                """
                SELECT
                    h.id,
                    h.title,
                    h.url,
                    h.mobile_url,
                    h.first_seen_at,
                    h.last_seen_at,
                    s.platform_id,
                    s.platform_name,
                    array_agg(DISTINCT ho.rank ORDER BY ho.rank) as ranks,
                    count(ho.id) as occurrence_count
                FROM headlines h
                JOIN sources s ON h.source_id = s.id
                JOIN headline_occurrences ho ON h.id = ho.headline_id
                WHERE h.title ILIKE %s
                  AND h.first_seen_at >= %s
                GROUP BY h.id, s.platform_id, s.platform_name
                ORDER BY occurrence_count DESC
                """,
                (f"%{keyword}%", today_start)
            )
        return cur.fetchall()


# ============================================================================
# Crawl Session Operations
# ============================================================================

def save_crawl_session(
    conn,
    sources_success: List[str],
    sources_failed: List[str],
    headline_count: int,
    started_at: datetime,
    completed_at: Optional[datetime] = None
) -> int:
    """Save a crawl session record.

    Args:
        conn: Database connection
        sources_success: List of successful platform IDs
        sources_failed: List of failed platform IDs
        headline_count: Number of headlines saved
        started_at: When crawl started
        completed_at: When crawl completed (defaults to now)

    Returns:
        Crawl session ID
    """
    if completed_at is None:
        completed_at = datetime.now()

    status = 'success' if not sources_failed else 'partial'

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO crawl_sessions
                (started_at, completed_at, sources_success, sources_failed, headline_count, status)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (started_at, completed_at, sources_success, sources_failed, headline_count, status)
        )
        return cur.fetchone()['id']


def get_recent_crawl_sessions(conn, limit: int = 10) -> List[Dict]:
    """Get recent crawl sessions.

    Returns:
        List of crawl session dictionaries
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT * FROM crawl_sessions
            ORDER BY started_at DESC
            LIMIT %s
            """,
            (limit,)
        )
        return cur.fetchall()


# ============================================================================
# Push Record Operations
# ============================================================================

def record_push(
    conn,
    push_type: str,
    channel: str,
    headline_count: int,
    pushed_at: datetime,
    status: str = 'success',
    error_message: Optional[str] = None
) -> int:
    """Record a push notification.

    Args:
        conn: Database connection
        push_type: Type of push ('daily', 'incremental', etc.)
        channel: Notification channel ('feishu', 'telegram', etc.)
        headline_count: Number of headlines in push
        pushed_at: When push was sent
        status: 'success' or 'failed'
        error_message: Error message if failed

    Returns:
        Push record ID
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO push_records
                (push_type, channel, headline_count, pushed_at, status, error_message)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (push_type, channel, headline_count, pushed_at, status, error_message)
        )
        return cur.fetchone()['id']


def get_today_push_records(conn, today_start: datetime) -> List[Dict]:
    """Get today's push records.

    Returns:
        List of push record dictionaries
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT * FROM push_records
            WHERE pushed_at >= %s
            ORDER BY pushed_at DESC
            """,
            (today_start,)
        )
        return cur.fetchall()


# ============================================================================
# Word Group Operations
# ============================================================================

def sync_word_groups_to_db(conn, word_groups: List[Dict]) -> int:
    """Sync word groups from config to database.

    Args:
        conn: Database connection
        word_groups: List of word group dictionaries with structure:
            {
                'required': ['word1'],
                'normal': ['word2', 'word3'],
                'group_key': 'word2 word3',
                'max_count': 0
            }

    Returns:
        Number of word groups synced
    """
    with conn.cursor() as cur:
        # Deactivate all existing groups
        cur.execute("UPDATE word_groups SET is_active = false")

        count = 0
        for position, group in enumerate(word_groups):
            group_key = group.get('group_key', '')
            max_count = group.get('max_count', 0)

            # Upsert word group
            cur.execute(
                """
                INSERT INTO word_groups (group_key, max_display_count, position, is_active)
                VALUES (%s, %s, %s, true)
                ON CONFLICT (id) DO UPDATE SET
                    group_key = EXCLUDED.group_key,
                    max_display_count = EXCLUDED.max_display_count,
                    position = EXCLUDED.position,
                    is_active = true
                RETURNING id
                """,
                (group_key, max_count, position)
            )
            group_id = cur.fetchone()['id']

            # Delete old words for this group
            cur.execute("DELETE FROM group_words WHERE group_id = %s", (group_id,))

            # Insert required words
            for word in group.get('required', []):
                cur.execute(
                    "INSERT INTO group_words (group_id, word, word_type) VALUES (%s, %s, 'required')",
                    (group_id, word)
                )

            # Insert normal words
            for word in group.get('normal', []):
                cur.execute(
                    "INSERT INTO group_words (group_id, word, word_type) VALUES (%s, %s, 'normal')",
                    (group_id, word)
                )

            count += 1

        return count


def get_active_word_groups(conn) -> List[Dict]:
    """Get all active word groups with their words.

    Returns:
        List of word group dictionaries
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                wg.id,
                wg.group_key,
                wg.max_display_count,
                wg.position,
                array_agg(
                    json_build_object('word', gw.word, 'type', gw.word_type)
                ) as words
            FROM word_groups wg
            LEFT JOIN group_words gw ON wg.id = gw.group_id
            WHERE wg.is_active = true
            GROUP BY wg.id
            ORDER BY wg.position
            """
        )
        return cur.fetchall()


# ============================================================================
# Daily Stats Operations
# ============================================================================

def update_daily_stats(conn, stat_date: datetime, source_id: int) -> None:
    """Update daily statistics for a source.

    Args:
        conn: Database connection
        stat_date: Date to calculate stats for
        source_id: Source to calculate stats for
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO daily_stats (stat_date, source_id, headline_count, unique_headlines, avg_rank)
            SELECT
                %s::date,
                %s,
                count(ho.id),
                count(DISTINCT h.id),
                avg(ho.rank)
            FROM headlines h
            JOIN headline_occurrences ho ON h.id = ho.headline_id
            WHERE h.source_id = %s
              AND h.first_seen_at::date = %s::date
            ON CONFLICT (stat_date, source_id) DO UPDATE SET
                headline_count = EXCLUDED.headline_count,
                unique_headlines = EXCLUDED.unique_headlines,
                avg_rank = EXCLUDED.avg_rank
            """,
            (stat_date, source_id, source_id, stat_date)
        )


def get_daily_stats(conn, start_date: datetime, end_date: datetime) -> List[Dict]:
    """Get daily statistics for a date range.

    Returns:
        List of daily stat dictionaries
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                ds.*,
                s.platform_id,
                s.platform_name
            FROM daily_stats ds
            JOIN sources s ON ds.source_id = s.id
            WHERE ds.stat_date BETWEEN %s AND %s
            ORDER BY ds.stat_date DESC, s.platform_name
            """,
            (start_date, end_date)
        )
        return cur.fetchall()
