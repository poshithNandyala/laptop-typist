@echo off
cd /d "%~dp0"

REM Kill any existing servers on ports 5000 and 8000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING') do (
    taskkill /PID %%a /F >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /PID %%a /F >nul 2>&1
)

REM Start Helper server in background
start /B "" python "%~dp0helper\typist_server.py" >nul 2>&1

REM Wait a moment for helper to start
ping -n 2 127.0.0.1 >nul

REM Start UI server in background
start /B "" python "%~dp0web-ui\server.py" >nul 2>&1
