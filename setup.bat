@echo off
REM Livestock Health System - Setup Script for Windows

echo ============================================================
echo    Livestock Health and Identification System
echo    Problem Statement 4 - Setup Script
echo ============================================================
echo.

REM Check if virtual environment exists
if not exist "myenv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please ensure myenv folder exists.
    pause
    exit /b 1
)

echo [1/4] Activating virtual environment...
call myenv\Scripts\activate.bat

echo.
echo [2/4] Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo [3/4] Checking installation...
python check_dependencies.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Dependency check failed!
    echo Please review the errors above.
    pause
    exit /b 1
)

echo.
echo [4/4] Setup complete!
echo.
echo ============================================================
echo    READY TO START
echo ============================================================
echo.
echo To run the system:
echo   1. python server_enhanced.py
echo   2. Open frontend/index.html in your browser
echo.
echo Or use: start_server.bat
echo.
pause
