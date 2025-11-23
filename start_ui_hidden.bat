@echo off
REM Start the Laptop Typist web UI server in the background (no console window)

cd /d "%~dp0web-ui"

start "" pythonw.exe -m http.server 8000
