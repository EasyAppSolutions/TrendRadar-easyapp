# TrendRadar - Project Context for Claude

## Overview

TrendRadar is a Chinese news aggregation and monitoring system that crawls trending headlines from multiple Chinese platforms (今日头条, 百度热搜, 知乎, bilibili, etc.), filters them by configurable keywords, and generates HTML reports. The project is being migrated from file-based storage to PostgreSQL for a Next.js frontend.

## Architecture

```
trendRadar/
├── main.py                 # Core Python crawler and report generator
├── config/
│   ├── config.yaml         # Main configuration (platforms, intervals, modes)
│   └── frequency_words.txt # Keyword groups for filtering headlines
├── db/                     # PostgreSQL integration module
│   ├── __init__.py
│   ├── connection.py       # Database connection handling
│   └── repository.py       # CRUD operations
├── html_templates/         # Modular HTML generation
│   ├── __init__.py
│   ├── styles.py           # CSS styles
│   ├── scripts.py          # JavaScript (accordion toggle)
│   └── components.py       # HTML component renderers
├── docker/
│   ├── docker-compose.yml  # PostgreSQL + crawler + nginx
│   ├── .env                # Environment variables (DB credentials)
│   ├── init.sql            # PostgreSQL schema
│   └── custom-entrypoint.sh # Installs psycopg2 at container start
├── output/                 # Generated reports (txt, html, json)
└── web/                    # Next.js frontend (TypeScript + Prisma)
    ├── prisma/schema.prisma
    ├── src/lib/prisma.ts
    └── src/app/api/headlines/route.ts
```

## Database

### Connection Priority
The system checks environment variables in this order:
1. `DB_CONNECTION_STRING` (preferred)
2. `DATABASE_URL`
3. Default: `postgresql://trendradar:changeme@localhost:5432/trendradar`

### Current Production Database
- **Provider**: DigitalOcean Managed PostgreSQL
- **Connection**: Set in `docker/.env` as `DB_CONNECTION_STRING`

### Key Tables
- `sources` - News platforms (toutiao, baidu, zhihu, bilibili, etc.)
- `headlines` - Individual news headlines with URLs
- `headline_occurrences` - Tracks rank changes over time
- `word_groups` / `group_words` - Keyword filtering configuration
- `crawl_sessions` - Crawl run logs
- `push_records` - Notification history

## Docker Setup

### Services
1. **postgres** - PostgreSQL 15 (local, used if no remote DB configured)
2. **trend-radar** - Python crawler container
3. **web** - Nginx serving static HTML reports on port 8050

### Running
```bash
cd docker
docker compose up -d
```

### Key Environment Variables (docker/.env)
- `DB_CONNECTION_STRING` - PostgreSQL connection URL
- `ENABLE_CRAWLER` - true/false
- `ENABLE_NOTIFICATION` - true/false
- `REPORT_MODE` - daily/incremental/current
- `CRON_SCHEDULE` - Cron expression (default: */30 * * * *)
- `RUN_MODE` - cron/once

## Python Crawler (main.py)

### Key Functions
- `save_titles_to_db()` - Saves crawled headlines to PostgreSQL
- `save_titles_to_file()` - Legacy file-based storage
- `read_all_today_titles()` - Reads from txt files
- `read_all_today_titles_from_db()` - Reads from PostgreSQL (with file fallback)
- `detect_new_titles_from_db()` - Finds new headlines since last push
- `render_html_content()` - Generates HTML reports

### Report Modes
- **daily** - All matching headlines for the day
- **incremental** - Only new headlines since last run
- **current** - Headlines from current crawl only

### Keyword Filtering (frequency_words.txt)
```
# Format: One group per paragraph, separated by blank lines
# Prefixes:
#   ! = required word (must contain)
#   - = filter word (exclude if contains)
#   @ = max display count (e.g., @5)
#   (none) = normal keyword

美国 日本 韩国
!特朗普
-广告
@10
```

## Next.js Frontend (web/)

### Tech Stack
- Next.js 16 with App Router
- TypeScript
- Tailwind CSS
- Prisma 6 (ORM)

### Setup
```bash
cd web
npm install
npx prisma generate
npm run dev
```

### API Endpoints
- `GET /api/headlines` - Returns headlines from last 24 hours, grouped by source

### Prisma Client Location
`web/src/lib/prisma.ts` - Singleton pattern for serverless/dev environments

## Common Tasks

### Adding a New Platform
1. Add platform config in `config/config.yaml` under `platforms`
2. The crawler will automatically create a new `sources` record

### Modifying Keyword Filters
Edit `config/frequency_words.txt` - changes take effect on next crawl

### Viewing Logs
```bash
docker compose logs trend-radar --tail 50
```

### Testing Database Connection
```bash
docker compose exec trend-radar python3 -c "from db import test_connection; print(test_connection())"
```

### Checking Headline Counts
```bash
docker compose exec trend-radar python3 -c "
from db import get_db_connection
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute('SELECT COUNT(*) FROM headlines')
        print(f'Total headlines: {cur.fetchone()[\"count\"]}')
"
```

## Notes

- The base Docker image (`wantcat/trendradar:latest`) does not include `psycopg2`, so `custom-entrypoint.sh` installs it at container startup
- Timezone is set to Beijing time (Asia/Shanghai) in docker-compose.yml, but user changed it to America/Edmonton
- HTML reports use accordion-style collapsible sections for keyword groups
- The crawler runs every 30 minutes by default (configurable via CRON_SCHEDULE)
