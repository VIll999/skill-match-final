#!/bin/bash

# Database Restoration Script for Skill Match Application
# This script restores the sample database with job data and skills

set -e

echo "📊 Restoring Skill Match Database..."
echo "===================================="

# Check if Docker is running
if ! docker-compose ps | grep -q "Up"; then
    echo "❌ Docker services are not running. Please start them first:"
    echo "   ./start.sh"
    exit 1
fi

# Check if backup file exists
if [ ! -f "database_backup.sql" ]; then
    echo "❌ Database backup file not found: database_backup.sql"
    echo "   This file should contain the sample data for the application."
    exit 1
fi

echo "📋 Backup file found: $(du -h database_backup.sql | cut -f1)"

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
until docker-compose exec -T db pg_isready -U dev -d skillmatch; do
    echo "   Database not ready yet, waiting..."
    sleep 2
done

echo "✅ Database is ready!"

# Restore the database
echo "📥 Restoring database from backup..."
docker-compose exec -T db psql -U dev -d skillmatch < database_backup.sql

echo ""
echo "✅ Database restoration completed!"
echo ""
echo "📊 Database Statistics:"

# Get some quick stats
echo "   Jobs: $(docker-compose exec -T db psql -U dev -d skillmatch -t -c "SELECT COUNT(*) FROM job_postings WHERE is_active = 1;" | tr -d ' ')"
echo "   Skills: $(docker-compose exec -T db psql -U dev -d skillmatch -t -c "SELECT COUNT(*) FROM emsi_skills;" | tr -d ' ')"
echo "   Users: $(docker-compose exec -T db psql -U dev -d skillmatch -t -c "SELECT COUNT(*) FROM users;" | tr -d ' ')"

echo ""
echo "🎉 Sample data restored successfully!"
echo "   You can now test the application with real job data."