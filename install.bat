@echo off
echo Installing Spotify Transcriber...
echo.

echo Installing Python dependencies...
cd backend
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error installing Python dependencies!
    pause
    exit /b 1
)
cd ..

echo.
echo Installing Node.js dependencies...
cd frontend
call npm install
if %errorlevel% neq 0 (
    echo Error installing Node.js dependencies!
    pause
    exit /b 1
)
cd ..

echo.
echo Installation complete!
echo.
echo To start the application, run: start_all.bat
echo Or start backend and frontend separately using start_backend.bat and start_frontend.bat
pause

