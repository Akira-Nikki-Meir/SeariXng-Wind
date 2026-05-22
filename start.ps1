# SearXNG Start - PowerShell
Write-Host "================================" -ForegroundColor Cyan
Write-Host " SearXNG (Windows)" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path "venv")) {
    Write-Host "[!] Virtual environment not found!" -ForegroundColor Red
    Write-Host "    Please run setup.ps1 first."
    Read-Host "Press Enter to exit"
    exit 1
}

& venv\Scripts\Activate.ps1

if (-not (Test-Path "settings.yml")) {
    Write-Host "[!] settings.yml not found!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[*] Starting SearXNG..." -ForegroundColor Green
Write-Host "[*] Open http://127.0.0.1:8888 in your browser"
Write-Host "[*] Press Ctrl+C to stop"
Write-Host ""

python wsgi.py
