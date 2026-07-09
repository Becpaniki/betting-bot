@echo off
echo Stopping Betting Bot...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *main_simple*" 2>nul
taskkill /F /IM python.exe 2>nul
echo Bot stopped!
pause
