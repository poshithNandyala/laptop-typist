@echo off
REM Start the Laptop Typist helper in the background (no console window)

REM %~dp0 = folder where this .bat lives
cd /d "%~dp0helper"

start "" pythonw.exe typist_server.py
