#!/bin/bash

# Skill Match Application Startup Script
# This script sets up and starts all services for the Skill Match application

set -e  # Exit on any error

echo "🚀 Starting Skill Match Application..."
echo "======================================"

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Setting up directories..."
mkdir -p secrets
mkdir -p logs

# Ensure environment files exist
echo "🔧 Checking environment configuration..."

# Check web UI environment
if [ ! -f "apps/web-ui/.env" ]; then
    echo "📝 Creating web UI environment file..."
    cp apps/web-ui/.env.example apps/web-ui/.env
fi

# Check if Adzuna secrets exist
if [ ! -f "secrets/.env.adzuna" ]; then
    echo "⚠️  Adzuna API credentials not found."
    echo "   Creating template file at secrets/.env.adzuna"
    echo "   Please add your Adzuna API credentials before running the scraper."
    cat > secrets/.env.adzuna << EOF
ADZUNA_APP_ID=your_adzuna_app_id_here
ADZUNA_APP_KEY=your_adzuna_app_key_here
EOF
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose down --remove-orphans

# Build and start all services
echo "🏗️  Building and starting services..."
echo "   This may take a few minutes on first run..."

# Start database first
echo "📊 Starting database..."
docker-compose up -d db

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Check if database is responding
until docker-compose exec -T db pg_isready -U dev -d skillmatch; do
    echo "   Database not ready yet, waiting..."
    sleep 5
done

echo "✅ Database is ready!"

# Check if we should restore sample data
if [ -f "database_backup.sql" ]; then
    echo "📊 Sample database found. Do you want to restore it? (y/n)"
    echo "   This will completely reset and populate the database with job postings and skills."
    echo "   (You can also run './clean-and-restore.sh' later)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "📥 Performing clean restore of sample data..."
        ./clean-and-restore.sh
    fi
fi

# Start API
echo "🔧 Starting API server..."
docker-compose up -d api

# Wait for API to be ready
echo "⏳ Waiting for API to be ready..."
sleep 15

# Check if API is responding
until curl -f http://localhost:8000/api/health > /dev/null 2>&1; do
    echo "   API not ready yet, waiting..."
    sleep 5
done

echo "✅ API is ready!"

# Start scraper (for daily job updates)
echo "📊 Starting job scraper..."
docker-compose up -d scraper

echo ""
echo "🎉 All services are starting up!"
echo "======================================"
echo ""
echo "📊 Service Status:"
echo "   • Database:  http://localhost:5442 (PostgreSQL)"
echo "   • API:       http://localhost:8000"
echo "   • Frontend:  http://localhost:5173 (start separately)"
echo ""
echo "🔗 Quick Links:"
echo "   • API Health:     http://localhost:8000/health"
echo "   • API Docs:       http://localhost:8000/docs"
echo "   • Job Statistics: http://localhost:8000/api/v1/jobs/stats"
echo ""
echo "📝 Next Steps:"
echo "   1. Start the frontend: cd apps/web-ui && npm run dev"
echo "   2. Open http://localhost:5173 in your browser"
echo "   3. Upload a resume to test the skill matching"
echo ""
echo "📊 To monitor services:"
echo "   docker-compose logs -f        # All services"
echo "   docker-compose logs -f api    # API only"
echo "   docker-compose logs -f scraper # Scraper only"
echo ""
echo "🛑 To stop all services:"
echo "   docker-compose down"
echo ""
echo "✨ Skill Match is ready to use!"