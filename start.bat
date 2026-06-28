@echo off
chcp 65001 >nul
REM ============================================================
REM   Commodity Dashboard - Start Script
REM ============================================================
cd /d "%~dp0"

echo ============================================================
echo   Commodity Dashboard
echo ============================================================
echo.

REM --- Check Python ---
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found.
    echo Install from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] Installing/checking libraries...
python -m pip install --quiet --upgrade yfinance pandas requests
echo       OK
echo.

echo [2/3] Downloading data (may take 1-2 minutes)...
echo.
python scripts\fetch_data.py
if errorlevel 1 (
    echo [ERROR] Failed to download data.
    pause
    exit /b 1
)
echo.

echo [3/3] Starting local web server on http://localhost:8000
echo       (keep this window open while using the dashboard)
echo.
start "" "http://localhost:8000"
python -m http.server 8000
