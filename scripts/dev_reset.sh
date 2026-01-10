#!/bin/bash
# Development reset script - Use this to start fresh

echo "🔄 Resetting development environment..."

# Stop containers
docker-compose down -v

# Remove SQLite database if exists
rm -f *.db

# Recreate database
python3 -c "from src.db.connection import init_db; init_db()"

echo "✅ Development environment reset complete!"
echo "Run: make run"
