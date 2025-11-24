@echo off
echo Starting UI + Helper...

start "" "%~dp0start_helper.bat"
timeout /t 1 >nul
start "" "%~dp0start_ui.bat"

exit
