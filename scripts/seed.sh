#!/bin/bash
# Database seeding script

set -e

DB_URL=${DATABASE_URL:-postgresql://localhost/scraping}

echo "🌱 Seeding database..."

psql "$DB_URL" -f databases/postgres/seeds/initial_data.sql

echo "✅ Seeding complete!"