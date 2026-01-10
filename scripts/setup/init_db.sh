#!/bin/bash
# Initialize production database

set -e

echo "🗄️  Initializing Matrix Treasury Database..."

# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
until pg_isready -h ${DB_HOST:-localhost} -p ${DB_PORT:-5432} -U ${DB_USER:-matrix}; do
  sleep 1
done

echo "PostgreSQL is ready!"

# Run migrations (if using Alembic)
if [ -d "alembic" ]; then
    echo "Running database migrations..."
    alembic upgrade head
fi

# Create initial admin user (if needed)
python3 scripts/setup/create_admin.py

echo "✅ Database initialization complete!"
