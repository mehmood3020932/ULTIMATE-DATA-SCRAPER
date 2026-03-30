#!/bin/bash
# Database migration script

set -e

DB_URL=${DATABASE_URL:-postgresql://localhost/scraping}

echo "🔄 Running migrations..."

# Run migrations in order
for migration in databases/postgres/migrations/*.sql; do
    echo "Applying $(basename $migration)..."
    psql "$DB_URL" -f "$migration"
done

echo "✅ Migrations complete!"