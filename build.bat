@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&^

echo ========================================
echo  Building SearXNG.exe
echo ========================================
echo.

:: Check Python
python --version >nul 2>&^1
if %errorlevel% neq 0 (
    echo [FAIL] Python not in PATH.
    pause
    exit /b 1
)
python --version
echo.

:: Create venv if needed
if not exist venv (
    echo [*] Creating venv...
    python -m venv venv
)
call venv\Scripts\activate.bat

:: Install build deps
echo [*] Installing build dependencies...
pip install customtkinter pyinstaller >nul 2>&^1
echo [OK] Dependencies ready.
echo.

:: Check required files
echo [*] Checking required files...
set /a missing=0
if not exist wsgi.py (echo [WARN] wsgi.py missing) ^& set /a missing+=1
if not exist mcp_server.py (echo [WARN] mcp_server.py missing) ^& set /a missing+=1
if not exist gui.py (echo [FAIL] gui.py missing) ^& set /a missing+=1
if not exist venv\Scripts\python.exe (echo [WARN] venv not set up) ^& set /a missing+=1
if !missing! gtr 0 echo [WARN] !missing! issue(s) found — build may fail.
if !missing! equ 0 echo [OK] All files present.
echo.

:: Build
echo [*] Building SearXNG.exe ...
pyinstaller --name SearXNG --onefile --windowed --clean ^
    --add-data "gui.py;." ^
    --add-data "mcp_server.py;." ^
    --add-data "wsgi.py;." ^
    --add-data "mcp_config.json;." ^
    --add-data "settings.yml;." ^
    gui.py

if %errorlevel% neq 0 (
    echo.
    echo [FAIL] Build failed.
    pause
    exit /b 1
)

echo.
echo ========================================
echo  Build Complete!
echo ========================================
echo.
echo  Output: dist\SearXNG.exe
echo.
echo  To make it portable:
echo    1. Copy SearXNG.exe to any folder
echo    2. Copy searx/, venv/, settings.yml alongside it
echo    3. Double-click SearXNG.exe
echo.
pause
