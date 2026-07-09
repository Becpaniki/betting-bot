@echo off
echo ========================================
echo Betting Bot - Setup Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

echo Python found!
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo Virtual environment created!
echo.

REM Activate virtual environment and install dependencies
echo Installing dependencies...
call venv\Scripts\activate
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Dependencies installed!
echo.

REM Create .env file if it doesn't exist
if not exist .env (
    echo Creating .env file...
    copy .env.example .env
    echo Please edit .env file and add your BOT_TOKEN
    echo Get token from @BotFather in Telegram
) else (
    echo .env file already exists
)

echo.
echo ========================================
echo Setup complete!
echo.
echo Next steps:
echo 1. Edit .env file and add your BOT_TOKEN
echo 2. Run: python init_db.py (to initialize database)
echo 3. Run: run.bat (to start the bot)
echo ========================================
pause
