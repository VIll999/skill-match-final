#!/bin/bash

# Complete Skill Match Application Startup Script
# Starts all services including frontend in development mode

set -e

echo "🚀 Starting Complete Skill Match Application..."
echo "=============================================="

# Check requirements
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."  
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ Node.js/npm is not installed. Please install Node.js first."
    echo "   Download from: https://nodejs.org/"
    exit 1
fi

# Start backend services
echo "🔧 Starting backend services..."
./start.sh

echo ""
echo "🎨 Setting up frontend..."

# Navigate to frontend and install dependencies
cd apps/web-ui

if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

# Start frontend in background
echo "🚀 Starting frontend development server..."
npm run dev &
FRONTEND_PID=$!

cd ../..

echo ""
echo "🎉 ALL SERVICES ARE RUNNING!"
echo "=============================================="
echo ""
echo "📊 Service URLs:"
echo "   • Frontend:  http://localhost:5173"
echo "   • API:       http://localhost:8000"
echo "   • Database:  localhost:5442"
echo ""
echo "🔗 Quick Links:"
echo "   • Application: http://localhost:5173"
echo "   • API Docs:    http://localhost:8000/docs"
echo "   • API Health:  http://localhost:8000/health"
echo ""
echo "📝 Usage:"
echo "   1. Open http://localhost:5173 in your browser"
echo "   2. Upload a resume (PDF/DOCX) to test skill extraction"
echo "   3. View job matches and skill analysis"
echo ""
echo "📊 Monitoring:"
echo "   docker-compose logs -f        # Backend services"
echo ""
echo "🛑 To stop all services:"
echo "   Press Ctrl+C, then run: docker-compose down"
echo ""

# Wait for interrupt
trap "echo ''; echo '🛑 Stopping all services...'; kill $FRONTEND_PID 2>/dev/null; docker-compose down; echo '✅ All services stopped.'; exit 0" INT

echo "✨ Application is ready! Press Ctrl+C to stop all services."
echo ""

# Keep script running
wait $FRONTEND_PID