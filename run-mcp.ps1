# SearXNG MCP Server Launcher - PowerShell
# Usage: .\run-mcp.ps1 [-Transport sse|stdio] [-Url http://localhost:8888]

param(
    [ValidateSet("stdio", "sse")]
    [string]$Transport = "stdio",

    [string]$Url,

    [switch]$StartSearxng,

    [switch]$Install
)

$venv_python = "venv\Scripts\python.exe"

if ($Install) {
    Write-Host "[*] Running installer..." -ForegroundColor Cyan
    if (Test-Path "install.ps1") {
        & .\install.ps1
    } else {
        Write-Host "[FAIL] install.ps1 not found." -ForegroundColor Red
    }
    exit 0
}

if ($StartSearxng) {
    Write-Host "[*] Starting SearXNG..." -ForegroundColor Cyan
    if (Test-Path "start.bat") {
        & .\start.bat
    } else {
        Write-Host "[FAIL] start.bat not found." -ForegroundColor Red
    }
    exit 0
}

# Check SearXNG
Write-Host "[*] Checking SearXNG..." -ForegroundColor Cyan
try {
    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8888/" -TimeoutSec 3 -ErrorAction Stop
    Write-Host "[OK] SearXNG is running." -ForegroundColor Green
} catch {
    Write-Host "[WARN] SearXNG may not be running. Start it with: .\run-mcp.ps1 -StartSearxng" -ForegroundColor Yellow
}

$args = @("mcp_server.py", "--transport", $Transport)
if ($Url) { $args += @("--url", $Url) }

Write-Host ""
Write-Host "=== SearXNG MCP Server ===" -ForegroundColor Cyan
Write-Host "Transport: $Transport"
Write-Host "URL:       $Url"
Write-Host ""
Write-Host "Use with Claude Code, Claude Desktop, or other MCP clients." -ForegroundColor DarkGray
Write-Host "Config file: mcp_config.json" -ForegroundColor DarkGray
Write-Host ""
Write-Host "Press Ctrl+C to stop" -ForegroundColor DarkGray
Write-Host ""

& $venv_python @args
