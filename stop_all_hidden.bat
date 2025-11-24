@echo off
echo Stopping all servers...

taskkill /IM python.exe /F >nul 2>&1
taskkill /IM pythonw.exe /F >nul 2>&1

echo Done.
exit
