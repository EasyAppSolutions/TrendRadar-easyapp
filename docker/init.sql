-- TrendRadar Database Schema
-- PostgreSQL 15+

-- ============================================================================
-- Core Tables
-- ============================================================================

-- News sources/platforms (Toutiao, Baidu, Bilibili, etc.)
CREATE TABLE IF NOT EXISTS sources (
    id SERIAL PRIMARY KEY,
    platform_id VARCHAR(50) UNIQUE NOT NULL,
    platform_name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Individual headlines
CREATE TABLE IF NOT EXISTS headlines (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES sources(id),
    title TEXT NOT NULL,
    url TEXT,
    mobile_url TEXT,
    first_seen_at TIMESTAMP NOT NULL,
    last_seen_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(source_id, title)
);

-- Track each time a headline appears with its rank
CREATE TABLE IF NOT EXISTS headline_occurrences (
    id SERIAL PRIMARY KEY,
    headline_id INTEGER REFERENCES headlines(id) ON DELETE CASCADE,
    rank INTEGER NOT NULL,
    crawled_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Keyword groups for filtering
CREATE TABLE IF NOT EXISTS word_groups (
    id SERIAL PRIMARY KEY,
    group_key VARCHAR(255) NOT NULL,
    max_display_count INTEGER DEFAULT 0,
    position INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Individual words within groups
CREATE TABLE IF NOT EXISTS group_words (
    id SERIAL PRIMARY KEY,
    group_id INTEGER REFERENCES word_groups(id) ON DELETE CASCADE,
    word VARCHAR(100) NOT NULL,
    word_type VARCHAR(20) NOT NULL CHECK (word_type IN ('required', 'normal', 'filter')),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Push/notification records
CREATE TABLE IF NOT EXISTS push_records (
    id SERIAL PRIMARY KEY,
    push_type VARCHAR(50) NOT NULL,
    channel VARCHAR(50) NOT NULL,
    headline_count INTEGER,
    pushed_at TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'success',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Crawl session logs
CREATE TABLE IF NOT EXISTS crawl_sessions (
    id SERIAL PRIMARY KEY,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    sources_success TEXT[],
    sources_failed TEXT[],
    headline_count INTEGER,
    status VARCHAR(20) DEFAULT 'running',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Daily statistics (pre-computed for performance)
CREATE TABLE IF NOT EXISTS daily_stats (
    id SERIAL PRIMARY KEY,
    stat_date DATE NOT NULL,
    source_id INTEGER REFERENCES sources(id),
    headline_count INTEGER,
    unique_headlines INTEGER,
    avg_rank DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(stat_date, source_id)
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_headlines_source ON headlines(source_id);
CREATE INDEX IF NOT EXISTS idx_headlines_first_seen ON headlines(first_seen_at);
CREATE INDEX IF NOT EXISTS idx_headlines_last_seen ON headlines(last_seen_at);
CREATE INDEX IF NOT EXISTS idx_headlines_title_search ON headlines USING gin(to_tsvector('simple', title));

CREATE INDEX IF NOT EXISTS idx_occurrences_headline ON headline_occurrences(headline_id);
CREATE INDEX IF NOT EXISTS idx_occurrences_crawled ON headline_occurrences(crawled_at);

CREATE INDEX IF NOT EXISTS idx_word_groups_active ON word_groups(is_active);
CREATE INDEX IF NOT EXISTS idx_group_words_group ON group_words(group_id);

CREATE INDEX IF NOT EXISTS idx_push_records_pushed ON push_records(pushed_at);
CREATE INDEX IF NOT EXISTS idx_crawl_sessions_started ON crawl_sessions(started_at);
CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON daily_stats(stat_date);

-- ============================================================================
-- Comments for documentation
-- ============================================================================

COMMENT ON TABLE sources IS 'News platforms being crawled (Toutiao, Baidu, etc.)';
COMMENT ON TABLE headlines IS 'Individual news headlines from all sources';
COMMENT ON TABLE headline_occurrences IS 'Track rank changes over time for each headline';
COMMENT ON TABLE word_groups IS 'Keyword groups for filtering headlines';
COMMENT ON TABLE group_words IS 'Individual keywords within each group';
COMMENT ON TABLE push_records IS 'History of notification pushes';
COMMENT ON TABLE crawl_sessions IS 'Log of each crawl run';
COMMENT ON TABLE daily_stats IS 'Pre-computed daily statistics per source';
