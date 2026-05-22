@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

:: ── SearXNG MCP Server Launcher ──────────────────────────────────────────────
:: Usage:
::   run-mcp.bat              - Start MCP server (stdio, for Claude Code)
::   run-mcp.bat sse          - Start MCP server (SSE, for custom clients)
::   run-mcp.bat --url URL    - Use custom SearXNG URL
::   run-mcp.bat list         - List available engines
::   run-mcp.bat start        - Start SearXNG instead
::   run-mcp.bat install      - Run full installer

if "%1"=="start" goto :start_searxng
if "%1"=="install" goto :install
if "%1"=="list" goto :list_engines

:: Check SearXNG is running first
echo [*] Checking SearXNG...
curl -s -o nul -w "%%{http_code}" "http://127.0.0.1:8888/" >nul 2>&1
if !errorlevel! neq 0 (
    echo [WARN] SearXNG may not be running.
    echo        Start it with: run-mcp.bat start
    echo.
)

if "%1"=="sse" (
    echo [*] Starting MCP server (SSE transport)...
    call venv\Scripts\activate.bat
    python mcp_server.py --transport sse
) else (
    echo [*] Starting MCP server (stdio transport)...
    echo [*] Use with Claude Code, Claude Desktop, or other MCP clients.
    echo [*] Config: mcp_config.json
    echo.
    call venv\Scripts\activate.bat
    python mcp_server.py --transport stdio
)
goto :eof

:list_engines
if not exist venv\Scripts\python.exe (
    echo [FAIL] Virtual environment not found. Run the installer first.
    pause
    exit /b 1
)
call venv\Scripts\activate.bat
python mcp_server.py --transport stdio --list 2>nul || python mcp_server.py --transport stdio
goto :eof

:start_searxng
echo [*] Starting SearXNG...
start.bat
goto :eof

:install
echo [*] Running installer...
install.ps1
goto :eof
