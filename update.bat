@echo off
chcp 65001 >nul
REM ============================================================
REM   Commodity Dashboard - Update Data + Restart Server
REM ============================================================
cd /d "%~dp0"

echo Updating data...
echo.
python scripts\fetch_data.py
if errorlevel 1 (
    echo [ERROR] Something went wrong.
    pause
    exit /b 1
)
echo.
echo Done! Refresh browser (F5) at http://localhost:8000
echo.
echo Starting server...
start "" "http://localhost:8000"
python -m http.server 8000
