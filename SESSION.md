# SearXNG on Windows — Session Notes

**Date:** 2026-05-20 / 2026-05-21
**Status:** Complete — SearXNG running at http://127.0.0.1:8888, GUI ready (`dist\SearXNG.exe`)
**Location:** `C:\Users\Saya\searxng-windows\`

---

## Vaporwave GUI (`gui.py`)

A standalone `.exe` built with PyInstaller that provides a vaporwave-themed, glass-like GUI for launching SearXNG and MCP Server as background processes. No command line needed.

### Features
- **Glass window** — Custom title bar (`overrideredirect(True)`), `wm_attributes("-alpha", 0.96)` for transparency, `-transparentcolor` blends frame into desktop
- **Draggable** — Header bar supports click-and-drag window movement
- **Process detection** — On startup, scans running python processes via `wmic` / PowerShell for `wsgi.py` and `mcp_server.py`; if found, shows green dot + "Stop" button
- **Background execution** — Services launch with `CREATE_NO_WINDOW`; closing the GUI does NOT stop services
- **Vaporwave palette** — Deep purple/black background, glowing green/red status dots, cyan text, pink accents

### Files
- **`gui.py`** — Main GUI application (customtkinter)
- **`build.bat`** — PyInstaller build script → `dist\SearXNG.exe`

### Build
```batch
build.bat
# Output: dist\SearXNG.exe (portable, double-click to run)
```

### Build dependencies
- `customtkinter` — UI framework (bundled by PyInstaller)
- `PyInstaller` — EXE builder (installed by build.bat)

### Notes
- The original crash (`ModuleNotFoundError: No module named 'customtkinter'`) occurs only when running `gui.py` with system Python instead of the venv. The `.exe` bundles all deps.
- Process detection falls back from `wmic` (deprecated on Win11) to PowerShell `Get-WmiObject`.

Make SearXNG usable on Windows without Docker.

---

## What's Different from Base SearXNG

This project adds a **wrapper layer** around upstream SearXNG to handle Windows compatibility and distribution. The SearXNG source itself (the `searx/` directory) is untouched upstream — all patches are applied locally by the installer.

### Wrapper layer (new files)

These files don't exist in upstream SearXNG and are specific to this Windows packaging:

- **[install.ps1](install.ps1)** — Dependency checker + full installer (not in upstream)
- **[run.bat](run.bat)** — Smart launcher routing to install/start/update (not in upstream)
- **[wsgi.py](wsgi.py)** — Custom WSGI entry point using waitress (upstream uses gunicorn/uWSGI)
- **[settings.yml](settings.yml)** — Windows-optimized config (upstream defaults to `/etc/searxng/settings.yml`)
- **[requirements.txt](requirements.txt)** — waitress dependency (upstream assumes gunicorn)
- **[setup.bat](setup.bat)** / **[setup.ps1](setup.ps1)** — Alternative install paths (not in upstream)
- **[start.bat](start.bat)** / **[start.ps1](start.ps1)** — Launch scripts (not in upstream)
- **[README.md](README.md)** — Documentation (not in upstream)

### Windows patches (applied at install time)

Four patches are applied by `install.ps1` to the cloned SearXNG source. These are **not** upstream-compatible — they break on Linux. Details and diffs:

- [Static/templates path resolution](#1-searxsearxinitpy-resolve-empty-statictemplates-paths) — `searx/searx/__init__.py`
- [pwd import guard](#2-searxsearxvalkeydbpy-pwd-import-windows-has-no-pwd) — `searx/searx/valkeydb.py`
- [Path separator normalization](#3-searxsearxwebutilspy-path-separator-normalization) — `searx/searx/webutils.py`
- [Static file copying](#4-setupbat-installps1-copy-static-assets-from-themessimple) — `searx/searx/static/` (post-install step)

### Configuration differences

| Setting | Base SearXNG | This Package | Why |
|---|---|---|---|
| `server.limiter` | defaults to false | explicitly false | No Valkey on Windows |
| `server.bind_address` | `0.0.0.0` | `127.0.0.1` | Security — local-only by default |
| `server.port` | 8888 (same) | 8888 (same) | |
| `ui.default_theme` | `simple` | `simple` | Only theme with working static files |
| `server.secret_key` | `ultrasecretkey` | random per install | Security |
| Settings location | `/etc/searxng/` | project root `settings.yml` | Windows portable |

---

## Final Project Structure

```
searxng-windows/
├── install.ps1           # Full installer with dependency check
├── run.bat               # Smart launcher: install / start / update
├── setup.bat             # Batch fallback (no PowerShell)
├── setup.ps1             # Legacy PowerShell setup
├── start.bat             # Launch server
├── start.ps1             # PowerShell launcher
├── wsgi.py               # WSGI entry point
├── settings.yml          # Auto-generated config
├── requirements.txt      # waitress dependency
├── README.md             # Documentation
├── .gitignore
├── searx/                # SearXNG source (cloned by installer)
└── venv/                 # Python virtual environment
```

---

## How Other Users Install It

```powershell
git clone <repo> C:\Users\<User>\searxng-windows
cd C:\Users\<User>\searxng-windows
.\install.ps1
.\run.bat start
# Open http://127.0.0.1:8888
```

`install.ps1` checks dependencies, clones SearXNG, installs deps, applies Windows patches, generates config, and clears cache.

---

## Windows Patches Applied to SearXNG Source

### 1. `searx/searx/__init__.py` — Resolve empty static/templates paths

**Problem:** When `static_path` and `templates_path` are empty strings in the YAML merge, the `SettingsDirectoryValue.__call__` fallback to defaults is never triggered because the YAML value is `""` (truthy string), not undefined.

**Fix:** After `settings.update(cfg)`, check for empty paths and set them from `searx_dir`:

```python
if not settings.get('ui', {}).get('static_path'):
    settings['ui']['static_path'] = os.path.join(searx_dir, 'static')
if not settings.get('ui', {}).get('templates_path'):
    settings['ui']['templates_path'] = os.path.join(searx_dir, 'templates')
```

### 2. `searx/searx/valkeydb.py` — `pwd` import (Windows has no pwd)

**Problem:** `import pwd` at top of file fails on Windows (`ModuleNotFoundError: No module named 'pwd'`).

**Fix:** Wrap in try/except:

```python
try:
    import pwd
except ImportError:
    pwd = None
```

And in `initialize()`:

```python
if pwd:
    _pw = pwd.getpwuid(os.getuid())
    logger.exception("[%s (%s)] can't connect valkey DB ...", _pw.pw_name, _pw.pw_uid)
else:
    logger.exception("can't connect valkey DB ...")
```

### 3. `searx/searx/webutils.py` — Path separator normalization

**Problem:** `os.path.join` produces backslashes on Windows (`simple\result_templates\default.html`), but `get_result_template()` in `webapp.py` constructs paths with forward slashes (`simple/result_templates/default.html`). Jinja2 can't find the template because the keys don't match.

**Fix:** In `get_result_templates()`, normalize to forward slashes:

```python
result_templates.add(f.replace('\\', '/'))
```

### 4. `setup.bat` / `install.ps1` — Copy static assets from `themes/simple/`

**Problem:** CSS/JS files live at `static/themes/simple/sxng-*.css` but templates reference them at `/static/sxng-*.css`. WhiteNoise serves from `static/` root.

**Fix:** During setup, copy the files:

```powershell
foreach ($f in (Get-ChildItem themes/simple -File | Where-Object { $_.Name -like "sxng-*" })) {
    Copy-Item $f.FullName (Join-Path static $f.Name) -Force
}
Copy-Item (Join-Path themes/simple img) (Join-Path static img) -Recurse -Force
```

---

## Known Issues

- **ahmia / torch engines:** Disabled — require Tor
- **startpage / brave engines:** Rate limited by upstream (CAPTCHA, 429). Normal on first use.
- **Git warning:** Non-critical, just skips version display
- **System load:** Minimal — ~50-100MB RAM idle, near-zero CPU. No background services.

---

## Dependencies Required on Target Machine

| Dependency | Min Version | Required? | Notes |
|---|---|---|---|
| Python | 3.10+ | Yes | Must be in PATH. Check "Add Python to PATH" during install. |
| Git | Any | Yes (with fallback) | Clones SearXNG source. Falls back to manual download. |
| PowerShell | 5.1+ | For install.ps1 | Built into Windows 10/11. setup.bat works without it. |

## Not Required

- Docker
- Redis / Valkey (optional, only for rate limiting)
- Nginx / Apache (waitress handles HTTP)
- WSL or Linux subsystem

---

## Files Created

### Core

| File | Purpose |
|---|---|
| `install.ps1` | Full installer with dependency check, progress output, Windows patches |
| `generate_settings.py` | Generates settings.yml with 118 engines from upstream defaults |
| `gui.py` | Vaporwave GUI launcher (customtkinter, glass window, process detection) |
| `build.bat` | PyInstaller build script → `dist\SearXNG.exe` |
| `mcp_server.py` | MCP server — wraps SearXNG search as Claude Code tools |
| `run-mcp.bat` | MCP server launcher (batch) |
| `run-mcp.ps1` | MCP server launcher (PowerShell) |
| `mcp_config.json` | Ready-to-use MCP config for Claude Code |
| `run.bat` | Smart launcher: `run.bat` / `run.bat start` / `run.bat update` |
| `setup.bat` | Batch installer (no PowerShell needed) |
| `setup.ps1` | Legacy PowerShell setup |
| `start.bat` | Launch SearXNG (checks for installation first) |
| `start.ps1` | PowerShell launcher |
| `wsgi.py` | WSGI entry point using waitress |
| `settings.yml` | SearXNG configuration (auto-generated by installer) |
| `requirements.txt` | waitress dependency |
| `.gitignore` | Exclude venv, settings.yml, cache |

### Documentation

| File | Purpose |
|---|---|
| `README.md` | Comprehensive documentation |
| `SESSION.md` | This file — session notes and technical details |
| `conversation.json` | Machine-readable conversation summary |

---

## Troubleshooting Commands

```powershell
# If templates not found:
Remove-Item __pycache__, searx\searx\__pycache__ -Recurse -Force

# If static files missing:
$theme = "searx\searx\static\themes\simple"
$static = "searx\searx\static"
Get-ChildItem $theme -File | Where-Object { $_.Name -like "sxng-*" } |
  ForEach-Object { Copy-Item $_.FullName $static -Force }

# Update SearXNG:
run.bat update
# or:
cd searx && git pull && cd .. && pip install -r searx/requirements.txt
```

---

## Security Notes

- Do **not** bind to `0.0.0.0` unless you understand the risks
- Do **not** set `public_instance: true` without rate limiting
- Keep `settings.yml` secure — it contains the `secret_key`
- The `secret_key` signs cookies and HMAC tokens

---

## MCP Server

An MCP server (`mcp_server.py`) is included that wraps SearXNG's search API as Claude Code tools.

### Tools (10 total)

| Tool | Description |
|---|---|
| `search` | Full search with all parameters (categories, language, time range, engines) |
| `search_quick` | Quick general search with defaults |
| `search_images` | Image search |
| `search_videos` | Video search |
| `search_its` | IT/developer search |
| `search_academic` | Academic/scientific search |
| `search_engine` | Single-engine search (e.g. `wikipedia`, `duckduckgo`) |
| `list_engines` | Discover available engines |
| `search_with_time` | Time-filtered search (day/week/month/year) |
| `search_multilang` | Language-specific search |

### Setup for Claude Code

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "searxng-search": {
      "command": "C:/Users/Saya/searxng-windows/venv/Scripts/python.exe",
      "args": ["C:/Users/Saya/searxng-windows/mcp_server.py", "--transport", "stdio"],
      "env": {}
    }
  }
}
```

### Launchers

- `run-mcp.bat` — Batch launcher (stdio by default)
- `run-mcp.ps1` — PowerShell launcher with params support
- `mcp_config.json` — Ready-to-use MCP config for Claude Code

---

## License

SearXNG: AGPL-3.0
This Windows packaging: AGPL-3.0
