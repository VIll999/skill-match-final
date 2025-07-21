@echo off
REM Skill Match Application Startup Script for Windows
REM This script sets up and starts backend services for the Skill Match application

echo 🚀 Starting Skill Match Application...
echo ======================================

REM Check if Docker is installed and running
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed or not running. Please install Docker Desktop first.
    echo    Download from: https://docs.docker.com/desktop/install/windows-install/
    pause
    exit /b 1
)

REM Create necessary directories
echo 📁 Setting up directories...
if not exist "secrets" mkdir secrets
if not exist "logs" mkdir logs

REM Ensure environment files exist
echo 🔧 Checking environment configuration...

REM Check web UI environment
if not exist "apps\web-ui\.env" (
    echo 📝 Creating web UI environment file...
    copy "apps\web-ui\.env.example" "apps\web-ui\.env"
)

REM Check if Adzuna secrets exist
if not exist "secrets\.env.adzuna" (
    echo ⚠️  Adzuna API credentials not found.
    echo    Creating template file at secrets\.env.adzuna
    echo    Please add your Adzuna API credentials before running the scraper.
    (
        echo ADZUNA_APP_ID=your_adzuna_app_id_here
        echo ADZUNA_APP_KEY=your_adzuna_app_key_here
    ) > "secrets\.env.adzuna"
)

REM Stop any existing containers
echo 🛑 Stopping existing containers...
docker-compose down --remove-orphans

REM Build and start all services
echo 🏗️  Building and starting services...
echo    This may take a few minutes on first run...

REM Start database first
echo 📊 Starting database...
docker-compose up -d db

REM Wait for database to be ready
echo ⏳ Waiting for database to be ready...
timeout /t 10 /nobreak >nul

REM Check if database is responding (simplified check for Windows)
echo ✅ Database should be ready!

REM Check if we should restore sample data
if exist "database_backup.sql" (
    echo 📊 Sample database found. Do you want to restore it? (y/n^)
    echo    This will populate the database with job postings and skills.
    echo    (You can also run 'restore-data.bat' later^)
    set /p response="Enter choice: "
    if /i "!response!"=="y" (
        echo 📥 Restoring sample data...
        call restore-data.bat
    )
)

REM Start API
echo 🔧 Starting API server...
docker-compose up -d api

REM Wait for API to be ready
echo ⏳ Waiting for API to be ready...
timeout /t 15 /nobreak >nul

echo ✅ API should be ready!

REM Start scraper (for daily job updates)
echo 📊 Starting job scraper...
docker-compose up -d scraper

echo.
echo 🎉 All backend services are running!
echo ======================================
echo.
echo 📊 Service Status:
echo    • Database:  localhost:5442 (PostgreSQL)
echo    • API:       http://localhost:8000
echo    • Frontend:  http://localhost:5173 (start separately)
echo.
echo 🔗 Quick Links:
echo    • API Health:     http://localhost:8000/health
echo    • API Docs:       http://localhost:8000/docs
echo    • Job Statistics: http://localhost:8000/api/v1/jobs/stats
echo.
echo 📝 Next Steps:
echo    1. Start the frontend: cd apps\web-ui ^&^& npm run dev
echo    2. Open http://localhost:5173 in your browser
echo    3. Upload a resume to test the skill matching
echo.
echo 📊 To monitor services:
echo    docker-compose logs -f        # All services
echo    docker-compose logs -f api    # API only
echo    docker-compose logs -f scraper # Scraper only
echo.
echo 🛑 To stop all services:
echo    docker-compose down
echo.
echo ✨ Backend services are ready! Start frontend separately.
echo Press any key to exit...
pause >nul