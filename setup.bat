@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

echo.
echo ========================================
echo  SearXNG Setup (Windows - Batch)
echo ========================================
echo.

:: ─── Dependency Checks ──────────────────────────────────────────────────────

:: Python check
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] Python is not installed or not in PATH.
    echo        Install from https://www.python.org/downloads/
    echo        IMPORTANT: Check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo [OK] Python %PYVER%

:: Git check (optional - just warn)
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] Git not found - SearXNG source cannot be cloned automatically.
    echo        Download from: https://git-scm.com/download/win
    echo        Or download manually: https://github.com/searxng/searxng/archive/refs/heads/master.zip
    goto :SKIP_GIT_CLONE
)

echo [OK] Git found

:: Clone SearXNG
if not exist searx\.git (
    echo.
    echo [*] Cloning SearXNG from GitHub...
    git config --global core.protectNTFS 2>nul
    git clone --depth 1 https://github.com/searxng/searxng.git searx
    if %errorlevel% neq 0 (
        echo [FAIL] Failed to clone SearXNG repository.
        pause
        exit /b 1
    )
    echo [OK] SearXNG cloned.
) else (
    echo [~] SearXNG source already present.
)

:SKIP_GIT_CLONE

:: Virtual environment
if not exist venv (
    echo.
    echo [*] Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [FAIL] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created.
) else (
    echo [~] Virtual environment already exists.
)

echo.
echo [*] Activating virtual environment...
call venv\Scripts\activate.bat

echo [*] Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1

echo.
echo [*] Installing SearXNG server dependencies...
pip install -r searx\requirements.txt
if %errorlevel% neq 0 (
    echo [FAIL] Failed to install server dependencies.
    pause
    exit /b 1
)
echo [OK] Server dependencies installed.

echo.
echo [*] Installing WSGI server (waitress)...
pip install waitress >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] Failed to install waitress.
    pause
    exit /b 1
)
echo [OK] waitress installed.

:: Fix static files
echo.
echo [*] Fixing static file paths...
if exist searx\searx\static\themes\simple (
    for %%f in (searx\searx\static\themes\simple\sxng-*.css searx\searx\static\themes\simple\sxng-*.js) do (
        if exist "%%f" copy /Y "%%f" "searx\searx\static\" >nul 2>&1
    )
    if not exist searx\searx\static\img (
        xcopy /E /I /Y "searx\searx\static\themes\simple\img" "searx\searx\static\img" >nul 2>&1
    )
    echo [OK] Static files fixed.
)

:: Settings check
if not exist settings.yml (
    echo.
    echo [*] No settings.yml found.
    echo     A default configuration will be created when you start SearXNG.
    echo     Edit it later at: settings.yml
)

echo.
echo ========================================
echo  Setup Complete!
echo ========================================
echo.
echo Next step: Run start.bat to launch SearXNG.
echo.
pause
