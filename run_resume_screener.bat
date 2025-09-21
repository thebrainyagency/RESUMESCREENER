@echo off
title Resume Screener
echo ==========================================
echo        Resume Screener - Starting...
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo.
    echo Please install Python 3.12+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo ✅ Python found
echo.

REM Check if we're in the right directory
if not exist "app.py" (
    echo ❌ app.py not found
    echo Please make sure you're running this from the ResumeScreener folder
    echo.
    pause
    exit /b 1
)

REM Install/update dependencies
echo 📦 Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo ✅ Dependencies installed
echo.

REM Start the Streamlit app
echo 🚀 Starting Resume Screener...
echo 🌐 Your browser should open automatically
echo 📋 If not, open: http://localhost:8501
echo.
echo ⚠️  To stop the app, close this window or press Ctrl+C
echo.

streamlit run app.py --server.headless false --server.port 8501

pause