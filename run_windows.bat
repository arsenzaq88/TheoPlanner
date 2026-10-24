@echo off
cd /d "%~dp0"
py -3 theoplanner.py
if errorlevel 1 python theoplanner.py
pause
