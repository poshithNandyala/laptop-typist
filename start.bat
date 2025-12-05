@echo off
echo ====================================
echo   Laptop Typist - Starting...
echo ====================================

cd /d "%~dp0"

REM Kill any existing servers on ports 5000 and 8000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING') do (
    taskkill /PID %%a /F >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /PID %%a /F >nul 2>&1
)

REM Start Helper server
echo Starting Helper server on port 5000...
start "Helper Server" cmd /k "cd helper && python typist_server.py"

timeout /t 2 >nul

REM Start UI server
echo Starting Web UI on port 8000...
start "UI Server" cmd /k "cd web-ui && python server.py"

timeout /t 2 >nul

echo.
echo ====================================
echo   Laptop Typist is running!
echo   Open: http://localhost:8000
echo ====================================
echo.
echo Press any key to close this window...
pause >nul
