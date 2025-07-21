@echo off
REM Complete Skill Match Application Startup Script for Windows
REM Starts all services including frontend in development mode

echo 🚀 Starting Complete Skill Match Application...
echo ==============================================

REM Check requirements
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed or not running. Please install Docker Desktop first.
    echo    Download from: https://docs.docker.com/desktop/install/windows-install/
    pause
    exit /b 1
)

where npm >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js/npm is not installed. Please install Node.js first.
    echo    Download from: https://nodejs.org/
    pause
    exit /b 1
)

REM Start backend services
echo 🔧 Starting backend services...
call start.bat

echo.
echo 🎨 Setting up frontend...

REM Navigate to frontend and install dependencies
cd apps\web-ui

if not exist "node_modules" (
    echo 📦 Installing frontend dependencies...
    npm install
)

REM Check if .env file exists
if not exist ".env" (
    echo 📝 Creating environment file...
    copy .env.example .env
)

REM Start frontend
echo 🚀 Starting frontend development server...
start "Frontend Server" cmd /k "npm run dev"

cd ..\..

echo.
echo 🎉 ALL SERVICES ARE RUNNING!
echo ==============================================
echo.
echo 📊 Service URLs:
echo    • Frontend:  http://localhost:5173
echo    • API:       http://localhost:8000
echo    • Database:  localhost:5442
echo.
echo 🔗 Quick Links:
echo    • Application: http://localhost:5173
echo    • API Docs:    http://localhost:8000/docs
echo    • API Health:  http://localhost:8000/health
echo.
echo 📝 Usage:
echo    1. Open http://localhost:5173 in your browser
echo    2. Upload a resume (PDF/DOCX) to test skill extraction
echo    3. View job matches and skill analysis
echo.
echo 📊 Monitoring:
echo    docker-compose logs -f        # Backend services
echo.
echo 🛑 To stop all services:
echo    Run: stop-all.bat
echo.
echo ✨ Application is ready! Frontend started in separate window.
echo Press any key to exit this script (services will continue running)...
pause >nul