@echo off
REM Stop All Services Script for Windows

echo 🛑 Stopping all Skill Match services...
echo =======================================

echo 📊 Stopping Docker containers...
docker-compose down

echo 🎨 Note: If frontend is running in a separate window, close that window to stop it.

echo.
echo ✅ All Docker services stopped!
echo    Frontend (if running separately) should be stopped manually.
echo.
echo Press any key to exit...
pause >nul