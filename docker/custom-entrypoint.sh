#!/bin/bash
set -e

# Install psycopg2 for PostgreSQL support
echo "📦 Installing psycopg2-binary..."
pip install psycopg2-binary -q 2>/dev/null || echo "⚠️ psycopg2 install failed, continuing..."

# Run the original entrypoint
exec /entrypoint.sh "$@"
