@echo off
cd /d "%~dp0"
py -3 -m pip install --upgrade pyinstaller
py -3 -m PyInstaller --noconfirm --clean --windowed --onefile --name TheoPlanner theoplanner.py
if errorlevel 1 python -m PyInstaller --noconfirm --clean --windowed --onefile --name TheoPlanner theoplanner.py
echo.
echo If successful, your app is in dist\TheoPlanner.exe
pause
