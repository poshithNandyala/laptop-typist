@echo off
echo Starting Helper server...

cd /d "%~dp0"
cd helper

REM Kill anything using port 5000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000') do (
    taskkill /PID %%a /F >nul 2>&1
)

start "Helper Server" cmd /k "python typist_server.py"
exit
