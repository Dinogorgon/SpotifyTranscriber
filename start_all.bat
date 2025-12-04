@echo off
echo ========================================
echo Starting Spotify Transcriber
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if Node.js is available
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    pause
    exit /b 1
)

echo Starting backend server...
start "Spotify Transcriber - Backend" cmd /k "cd /d %~dp0backend && python main.py"
timeout /t 3 /nobreak >nul

echo Starting frontend server...
start "Spotify Transcriber - Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================
echo Both servers are starting...
echo ========================================
echo Backend API: http://localhost:8000
echo Frontend App: http://localhost:5173 (or check the frontend window)
echo.
echo.
echo NOTE: In PowerShell, use: .\start_all.bat
echo.
echo Press any key to close this window (servers will continue running)
pause >nul

