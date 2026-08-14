@echo off
title SunKing LPG Inventory

cd /d "C:\Users\imbai\sunking-lpg-inventory"

if not exist "venv\Scripts\python.exe" (
    echo.
    echo ERROR: Virtual environment not found.
    echo.
    pause
    exit /b
)

echo Starting SunKing LPG Inventory...
echo.

start "" "http://127.0.0.1:8000/"

"venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000

pause