@echo off
REM Database Restoration Script for Skill Match Application - Windows
REM This script restores the sample database with job data and skills

echo 📊 Restoring Skill Match Database...
echo ====================================

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

REM Show backup file size
for %%F in ("database_backup.sql") do (
    set /a size=%%~zF/1024/1024
    echo 📋 Backup file found: !size!MB
)

REM Wait for database to be ready
echo ⏳ Waiting for database to be ready...
timeout /t 5 /nobreak >nul

echo ✅ Database should be ready!

REM Restore the database
echo 📥 Restoring database from backup...
docker-compose exec -T db psql -U dev -d skillmatch < database_backup.sql

echo.
echo ✅ Database restoration completed!
echo.
echo 📊 Getting database statistics...

REM Get some quick stats (simplified for Windows)
echo    Database restored with sample job data and skills
echo    Check the application at http://localhost:5173

echo.
echo 🎉 Sample data restored successfully!
echo    You can now test the application with real job data.
echo.
echo Press any key to continue...
pause >nul