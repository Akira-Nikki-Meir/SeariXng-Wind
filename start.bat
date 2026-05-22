@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

:: Check if installation is complete
if not exist venv (
    echo.
    echo ========================================
    echo  SearXNG not installed yet
    echo ========================================
    echo.
    echo Run the installer first:
    echo   install.ps1   (PowerShell)
    echo   or
    echo   setup.bat     (batch, simpler)
    echo.
    pause
    exit /b 1
)

:: Activate venv
call venv\Scripts\activate.bat

if not exist settings.yml (
    echo [!] settings.yml not found!
    pause
    exit /b 1
)

echo.
echo ========================================
echo  SearXNG (Windows)
echo ========================================
echo.
echo Starting on http://127.0.0.1:8888
echo Press Ctrl+C to stop
echo.

python wsgi.py
