@echo off
setlocal enabledelayedexpansion

:: ── SearXNG Launcher for Windows ────────────────────────────────────────────
:: This script intelligently finds and runs the best available installer.
::
:: Usage:
::   run.bat              - Install or update SearXNG
::   run.bat install      - Fresh install (same as above)
::   run.bat setup        - Quick setup without PowerShell
::   run.bat start        - Start SearXNG
::   run.bat update       - Update SearXNG to latest version

if "%1"=="start" goto start

if "%1"=="update" goto update

:: Default: try PowerShell installer, fall back to batch setup

if exist install.ps1 (
    powershell -ExecutionPolicy Bypass -File "%~dp0install.ps1"
    goto :eof
)

echo.
echo [!] install.ps1 not found, falling back to setup.bat
echo.
call "%~dp0setup.bat"
goto :eof

:update
if exist searx\.git (
    cd /d "%~dp0searx"
    git pull
    cd /d "%~dp0"
    if exist venv\Scripts\python.exe (
        call venv\Scripts\activate.bat
        pip install -r searx\requirements.txt
    )
    echo.
    echo [OK] SearXNG updated.
) else (
    echo [FAIL] SearXNG not found. Run "run.bat" first to install.
)
goto :eof

:start
call "%~dp0start.bat"
goto :eof
