# SearXNG Windows Installer
# -------------------------
# A self-contained installer for SearXNG (no Docker).
# Run from PowerShell: .\install.ps1

#Requires -Version 5.1
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# ─── Colors ───────────────────────────────────────────────────────────────────
$ColorOk     = "Green"
$ColorWarn   = "Yellow"
$ColorFail   = "Red"
$ColorInfo   = "Cyan"
$ColorHeader = "Magenta"

function Write-Ok    { Write-Host "[OK]" -ForegroundColor $ColorOk -NoNewline; Write-Host " $args" }
function Write-Warn  { Write-Host "[WARN]" -ForegroundColor $ColorWarn -NoNewline; Write-Host " $args" }
function Write-Fail  { Write-Host "[FAIL]" -ForegroundColor $ColorFail -NoNewline; Write-Host " $args" }
function Write-Info  { Write-Host "[*]" -ForegroundColor $ColorInfo -NoNewline; Write-Host " $args" }
function Write-Header { Write-Host "`n=== $args ===" -ForegroundColor $ColorHeader }

# ─── Dependency Checks ────────────────────────────────────────────────────────
$deps_ok = $true
$missing = @()

Write-Header "Dependency Check"

# Python
Write-Info "Checking Python 3.10+..."
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Fail "Python not found in PATH."
    Write-Host "    Install from https://www.python.org/downloads/" -ForegroundColor DarkYellow
    Write-Host "    IMPORTANT: Check 'Add Python to PATH' during installation."
    $deps_ok = $false
    $missing += "Python 3.10+"
} else {
    try {
        $py_ver = & python --version 2>&1
        $py_ver_str = $py_ver -replace "Python ", ""
        $py_ver_parsed = [version]($py_ver_str.TrimEnd())
        if ($py_ver_parsed.Major -lt 3 -or ($py_ver_parsed.Major -eq 3 -and $py_ver_parsed.Minor -lt 10)) {
            Write-Fail "Python $py_ver_str found, but 3.10+ required."
            $deps_ok = $false
            $missing += "Python 3.10+"
        } else {
            Write-Ok "Python $py_ver_str"
        }
    } catch {
        Write-Fail "Could not determine Python version."
        $deps_ok = $false
        $missing += "Python 3.10+"
    }
}

# Git
Write-Info "Checking Git..."
$git = Get-Command git -ErrorAction SilentlyContinue
if (-not $git) {
    Write-Warn "Git not found in PATH."
    Write-Host "    SearXNG source will be downloaded. Install Git to enable updates." -ForegroundColor DarkYellow
    Write-Host "    Download: https://git-scm.com/download/win"
    Write-Host "    You can also install dependencies manually with: pip install -r searx/requirements.txt"
    Write-Host "    [Continuing without Git - you'll need to download SearXNG manually]" -ForegroundColor DarkYellow
    $deps_ok = $false
    $missing += "Git"
} else {
    $git_ver = & git --version 2>&1
    Write-Ok "$git_ver"
}

# ─── Fail if critical deps missing ───────────────────────────────────────────
if (-not $deps_ok) {
    Write-Header "Missing Dependencies"
    Write-Fail "The following are required: $($missing -join ', ')"
    Write-Host ""
    Write-Host "Please install the missing dependencies and run this script again." -ForegroundColor Yellow
    if ($input) { Read-Host "Press Enter to exit" }
    exit 1
}

# ─── Prepare Directories ─────────────────────────────────────────────────────
Write-Header "Preparing Environment"

$script_dir = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not (Test-Path "venv")) {
    Write-Info "Creating Python virtual environment..."
    python -m venv venv
    if ($LASTEXITCODE -ne 0) { Write-Fail "Failed to create virtual environment."; exit 1 }
    Write-Ok "Virtual environment created."
} else {
    Write-Ok "Virtual environment already exists."
}

Write-Info "Activating virtual environment..."
. .\venv\Scripts\Activate.ps1

# ─── Upgrade pip ──────────────────────────────────────────────────────────────
Write-Header "Upgrading pip"
python -m pip install --upgrade pip
Write-Ok "pip upgraded to $(python -m pip --version | Select-String '\d+\.\d+\.\d+' | ForEach-Object { $_.Matches[0].Value })"

# ─── Clone SearXNG or download manually ──────────────────────────────────────
Write-Header "Getting SearXNG"

if (Test-Path "searx\.git") {
    Write-Ok "SearXNG source already cloned."
} elseif ($git) {
    Write-Info "Cloning SearXNG from GitHub..."
    git config --global core.protectNTFS 2>$null
    git clone --depth 1 https://github.com/searxng/searxng.git searx
    if ($LASTEXITCODE -ne 0) { Write-Fail "Failed to clone SearXNG repository."; exit 1 }
    Write-Ok "SearXNG cloned successfully."
} else {
    Write-Header "Manual Download Required"
    Write-Host ""
    Write-Host "Git is not installed, so SearXNG cannot be cloned automatically." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please download SearXNG manually:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  1. Download: https://github.com/searxng/searxng/archive/refs/heads/master.zip" -ForegroundColor DarkYellow
    Write-Host "  2. Extract to: $(Resolve-Path .)\searx\" -ForegroundColor DarkYellow
    Write-Host "  3. Run this script again (it will detect the existing searx folder)" -ForegroundColor DarkYellow
    Write-Host ""
    Write-Host "Or install Git and re-run this installer:" -ForegroundColor DarkYellow
    Write-Host "    winget install Git.Git" -ForegroundColor Gray
    Write-Host ""
    Write-Fail "Cannot proceed without SearXNG source."
    if ($input) { Read-Host "Press Enter to exit" }
    exit 1
}

# ─── Install Dependencies ────────────────────────────────────────────────────
Write-Header "Installing SearXNG Dependencies"

Write-Info "Installing server dependencies from searx/requirements.txt..."
pip install -r searx\requirements.txt
if ($LASTEXITCODE -ne 0) { Write-Fail "Failed to install server dependencies."; exit 1 }
Write-Ok "Server dependencies installed."

if (Test-Path "requirements.txt") {
    Write-Info "Installing WSGI server (waitress)..."
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { Write-Fail "Failed to install waitress."; exit 1 }
    Write-Ok "waitress installed."
}

# ─── Fix Static Files ────────────────────────────────────────────────────────
Write-Header "Fixing Static File Paths"

$theme_static = "searx/searx/static/themes/simple"
if (Test-Path $theme_static) {
    $static_root = "searx/searx/static"
    $copied = 0
    foreach ($f in (Get-ChildItem $theme_static -File | Where-Object { $_.Name -like "sxng-*" })) {
        Copy-Item $f.FullName (Join-Path $static_root $f.Name) -Force
        $copied++
    }
    $img_dst = Join-Path $static_root "img"
    if (-not (Test-Path $img_dst)) {
        Copy-Item (Join-Path $theme_static "img") $img_dst -Recurse -Force
    }
    Write-Ok "Copied $copied CSS/JS files to static root, plus favicon images."
} else {
    Write-Warn "No static files found at $theme_static"
}

# ─── Apply Windows Patches ──────────────────────────────────────────────────
Write-Header "Applying Windows Compatibility Patches"

$patches_applied = 0

# Patch 1: pwd import in valkeydb.py
$valkeydb = "searx/searx/valkeydb.py"
if (Test-Path $valkeydb) {
    $content = Get-Content $valkeydb -Raw
    if ($content -match "^\s*import pwd\s*$") {
        $content = $content -replace "^\s*import pwd\s*$", "try:`n    import pwd`nexcept ImportError:`n    pwd = None"
        Set-Content $valkeydb $content -NoNewline
        $patches_applied++
        Write-Ok "Patch 1: valkeydb.py - pwd import (Windows compatibility)"
    } else {
        Write-Ok "Patch 1: valkeydb.py - already patched."
    }
}

# Patch 2: pwd usage in valkeydb.py
if (Test-Path $valkeydb) {
    $content = Get-Content $valkeydb -Raw
    if ($content -match "pwd\.getpwuid\(os\.getuid\(\)\)") {
        $content = $content -replace "(\s+)if pwd:", "`$1try:`n`$1    if pwd:"
        $content = $content -replace "(\s+pwd = pwd\.getpwuid\(os\.getuid\(\)\))", "`$1`n`$1except AttributeError:`n`$1    _pw = None"
        $content = $content -replace "(\s+)logger\.exception\(\[.*can't connect valkey.*", "`$1if _pw:`n`$1    logger.exception(`"`$1        [`$1        $_pw.pw_name, `_pw.pw_uid`$1    ] can't connect valkey DB ...`$1        `"`$1    )`$1else:`$1        logger.exception(`"can't connect valkey DB ...`")"
        Set-Content $valkeydb $content -NoNewline
        $patches_applied++
        Write-Ok "Patch 2: valkeydb.py - pwd usage (Windows compatibility)"
    }
}

# Patch 3: Path separator in webutils.py
$webutils = "searx/searx/webutils.py"
if (Test-Path $webutils) {
    $content = Get-Content $webutils -Raw
    if ($content -match "result_templates\.add\(f\)") {
        $content = $content -replace "result_templates\.add\(f\)", "result_templates.add(f.replace('\\\\', '/'))"
        Set-Content $webutils $content -NoNewline
        $patches_applied++
        Write-Ok "Patch 3: webutils.py - path separator normalization"
    } else {
        Write-Ok "Patch 3: webutils.py - already patched."
    }
}

# Patch 4: Static/templates path resolution in __init__.py
$init_file = "searx/searx/__init__.py"
if (Test-Path $init_file) {
    $content = Get-Content $init_file -Raw
    if ($content -notmatch "static_path.*searx_dir.*static") {
        $insert = @'

    # Resolve empty static_path and templates_path to defaults (Windows YAML merge bug)
    if not settings.get('ui', {}).get('static_path'):
        settings['ui']['static_path'] = os.path.join(searx_dir, 'static')
    if not settings.get('ui', {}).get('templates_path'):
        settings['ui']['templates_path'] = os.path.join(searx_dir, 'templates')
'@
        $content = $content -replace "(settings\.update\(cfg\))", "`$1$insert"
        Set-Content $init_file $content -NoNewline
        $patches_applied++
        Write-Ok "Patch 4: __init__.py - static/templates path resolution"
    } else {
        Write-Ok "Patch 4: __init__.py - already patched."
    }
}

if ($patches_applied -eq 0) {
    Write-Ok "All patches already applied."
}

# ─── Settings ─────────────────────────────────────────────────────────────────
Write-Header "Configuration"

if (-not (Test-Path "settings.yml")) {
    Write-Info "Generating settings.yml from upstream defaults..."
    python generate_settings.py settings.yml
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "Failed to generate settings.yml."
        exit 1
    }
} else {
    Write-Ok "settings.yml already exists."
}

# ─── Clear Python Cache ──────────────────────────────────────────────────────
Write-Header "Cleaning Up"

$cache_dirs = @(
    "__pycache__",
    "venv\Lib\site-packages\__pycache__",
    "searx\searx\__pycache__"
)
foreach ($cache in $cache_dirs) {
    if (Test-Path $cache) {
        Remove-Item $cache -Recurse -Force -ErrorAction SilentlyContinue
    }
}
Write-Ok "Python cache cleared."

# ─── Done ────────────────────────────────────────────────────────────────────
Write-Header "Installation Complete!"
Write-Host ""
Write-Host "  SearXNG is ready!" -ForegroundColor Green
Write-Host ""
Write-Host "  To start SearXNG:" -ForegroundColor Cyan
Write-Host "    start.bat" -ForegroundColor White
Write-Host ""
Write-Host "  Or (PowerShell):" -ForegroundColor Cyan
Write-Host "    start.ps1" -ForegroundColor White
Write-Host ""
Write-Host "  Then open: http://127.0.0.1:8888" -ForegroundColor Green
Write-Host ""
Write-Host "  To update SearXNG later:" -ForegroundColor Cyan
Write-Host "    cd searx && git pull && cd .. && pip install -r searx/requirements.txt" -ForegroundColor White
Write-Host ""
if ($input) { Read-Host "Press Enter to close" }
