#!/bin/bash

# Frontend Startup Script for Skill Match Application

echo "🎨 Starting Skill Match Frontend..."
echo "=================================="

# Check if we're in the right directory
if [ ! -f "apps/web-ui/package.json" ]; then
    echo "❌ Please run this script from the skill-match root directory"
    exit 1
fi

# Check if Node.js is installed
if ! command -v npm &> /dev/null; then
    echo "❌ Node.js/npm is not installed. Please install Node.js first."
    echo "   Download from: https://nodejs.org/"
    exit 1
fi

# Navigate to frontend directory
cd apps/web-ui

# Check if dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📝 Creating environment file..."
    cp .env.example .env
fi

# Start the development server
echo "🚀 Starting development server..."
echo "   Frontend will be available at: http://localhost:5173"
echo "   Press Ctrl+C to stop"
echo ""

npm run dev