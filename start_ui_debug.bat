@echo off
cd /d "%~dp0"
cd web-ui

echo Starting UI with pythonw and logging...
pythonw.exe server.py > ui_log.txt 2>&1

echo If UI does not load, open ui_log.txt to see the error.
pause
