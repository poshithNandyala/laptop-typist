@echo off
echo Starting UI server...

REM Change to folder of THIS BAT file
cd /d "%~dp0"
cd web-ui

REM Kill anything using port 8000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do (
    taskkill /PID %%a /F >nul 2>&1
)

start "UI Server" cmd /k "python server.py"
exit
