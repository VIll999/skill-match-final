@echo off
REM Frontend Startup Script for Skill Match Application - Windows

echo 🎨 Starting Skill Match Frontend...
echo ==================================

REM Check if we're in the right directory
if not exist "apps\web-ui\package.json" (
    echo ❌ Please run this script from the skill-match root directory
    pause
    exit /b 1
)

REM Check if Node.js is installed
where npm >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js/npm is not installed. Please install Node.js first.
    echo    Download from: https://nodejs.org/
    pause
    exit /b 1
)

REM Navigate to frontend directory
cd apps\web-ui

REM Check if dependencies are installed
if not exist "node_modules" (
    echo 📦 Installing dependencies...
    npm install
)

REM Check if .env file exists
if not exist ".env" (
    echo 📝 Creating environment file...
    copy .env.example .env
)

REM Start the development server
echo 🚀 Starting development server...
echo    Frontend will be available at: http://localhost:5173
echo    Press Ctrl+C to stop
echo.

npm run dev