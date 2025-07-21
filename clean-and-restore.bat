@echo off
setlocal enabledelayedexpansion
REM Clean Database and Restore Script for Windows
REM This script completely resets the database and restores from backup

echo 🗑️  Clean Database and Restore Data...
echo =====================================

REM Check if Docker is running
docker-compose ps >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker services are not running. Please start them first:
    echo    start.bat
    pause
    exit /b 1
)

REM Check if backup file exists
if not exist "database_backup.sql" (
    echo ❌ Database backup file not found: database_backup.sql
    echo    This file should contain the sample data for the application.
    pause
    exit /b 1
)

echo ⚠️  WARNING: This will completely reset your database!
echo    All existing data will be lost.
echo.
set /p confirm="Are you sure you want to continue? (y/n): "
if /i not "!confirm!"=="y" (
    echo Cancelled.
    pause
    exit /b 0
)

echo.
echo 🛑 Stopping API service...
docker-compose stop api

echo.
echo 🗑️  Dropping and recreating database...
docker-compose exec -T db psql -U dev -d postgres -c "DROP DATABASE IF EXISTS skillmatch;"
docker-compose exec -T db psql -U dev -d postgres -c "CREATE DATABASE skillmatch;"

echo.
echo 📥 Restoring database from backup...
docker-compose exec -T db psql -U dev -d skillmatch < database_backup.sql

echo.
echo 🔧 Fixing database sequences...
docker-compose exec -T db psql -U dev -d skillmatch -c "SELECT setval('skill_alignment_snapshots_id_seq', (SELECT COALESCE(MAX(id), 0) + 1 FROM skill_alignment_snapshots));"
docker-compose exec -T db psql -U dev -d skillmatch -c "SELECT setval('user_industry_alignment_id_seq', (SELECT COALESCE(MAX(id), 0) + 1 FROM user_industry_alignment));"
docker-compose exec -T db psql -U dev -d skillmatch -c "SELECT setval('user_skill_history_id_seq', (SELECT COALESCE(MAX(id), 0) + 1 FROM user_skill_history));"

echo.
echo 🔄 Restarting API service...
docker-compose start api

echo.
echo ⏳ Waiting for API to be ready...
timeout /t 10 /nobreak >nul

echo.
echo ✅ Database cleaned and restored successfully!
echo.
echo 📊 You can now test the application:
echo    • Frontend: http://localhost:5173
echo    • API Health: http://localhost:8000/api/health
echo    • API Docs: http://localhost:8000/docs
echo.
echo Press any key to continue...
pause >nul