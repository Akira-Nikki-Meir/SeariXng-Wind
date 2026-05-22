# SearXNG Setup - PowerShell
Write-Host "================================" -ForegroundColor Cyan
Write-Host " SearXNG Setup (Windows)" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
try {
    $pyVersion = python --version 2>&1
    Write-Host "Python: $pyVersion"
} catch {
    Write-Host "[!] Python is not installed or not in PATH." -ForegroundColor Red
    Write-Host "    Install Python 3.10+ from https://www.python.org/downloads/"
    Write-Host "    Make sure to check 'Add Python to PATH' during installation."
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Create venv if not exists
if (-not (Test-Path "venv")) {
    Write-Host "[*] Creating virtual environment..."
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[!] Failed to create virtual environment." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "[OK] Virtual environment created." -ForegroundColor Green
} else {
    Write-Host "[~] Virtual environment already exists."
}

Write-Host ""
Write-Host "[*] Activating virtual environment..."
& venv\Scripts\Activate.ps1

Write-Host "[*] Upgrading pip..."
python -m pip install --upgrade pip

Write-Host "[*] Installing SearXNG and dependencies..."
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] Failed to install dependencies." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
if (-not (Test-Path "settings.yml")) {
    Write-Host "[!] settings.yml not found!" -ForegroundColor Red
    Write-Host "    Please create a settings.yml file in this directory."
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host " Setup complete!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next: Edit settings.yml, then run: .\start.bat"
Read-Host "Press Enter to finish"
