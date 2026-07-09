@echo off
echo Starting Betting Bot...
echo Bot will run in background.
echo To stop: close this window or run stop_bot.bat
echo.
cd /d "%~dp0"
start "" /B "%~dp0venv\Scripts\python.exe" main_simple.py
echo Bot started! You can close this window.
timeout /t 5
