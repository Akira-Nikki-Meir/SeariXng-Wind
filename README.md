# SearXNG for Windows (No Docker)

A self-contained installation of [SearXNG](https://github.com/searxng/searxng)
for Windows. Runs entirely on Python — no Docker, no WSL, no external
databases required.

## What is SearXNG?

SearXNG is a free internet metasearch engine which aggregates results from
various search services and databases. Users are neither tracked nor profiled.

## Requirements

### Mandatory

| Dependency | Minimum | Why |
|---|---|---|
| **Python** | 3.10+ | SearXNG runs on Python. Download from [python.org](https://www.python.org/downloads/). **Check "Add Python to PATH"** during installation. |
| **Git** | Any | Clones the SearXNG source. Install via `winget install Git.Git` or [git-scm.com](https://git-scm.com/download/win). |

### Optional

| Dependency | Why |
|---|---|
| **PowerShell 5.1+** | The install script uses PowerShell features (built into Windows 10/11). |
| **Git Bash** | Alternative shell if you prefer bash on Windows. |

### Not Required

- Docker (the whole point of this installation)
- Redis / Valkey (optional, only used for rate limiting)
- Nginx / Apache (waitress handles HTTP serving)
- WSL or Linux subsystem

## Quick Start

```powershell
# 1. Clone this project
git clone <your-fork-url> C:\Users\<YourName>\searxng-windows
cd C:\Users\<YourName>\searxng-windows

# 2. Run the installer (checks dependencies, installs everything)
.\install.ps1

# 3. Start SearXNG
.\start.bat

# 4. Open in browser
# http://127.0.0.1:8888
```

### PowerShell Execution Policy

If you get an execution policy error:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Project Structure

```
searxng-windows/
├── install.ps1          # Full installer with dependency check
├── start.bat            # Launch SearXNG (batch)
├── start.ps1            # Launch SearXNG (PowerShell)
├── setup.bat            # Legacy installer (batch, simpler)
├── settings.yml         # SearXNG configuration (auto-generated)
├── requirements.txt     # WSGI server dependency (waitress)
├── .gitignore
├── searx/               # SearXNG source (cloned by installer)
│   ├── searx/           # Python package
│   ├── requirements.txt # Server dependencies
│   └── ...
├── venv/                # Python virtual environment
└── __pycache__/         # Python cache (ignored)
```

## Configuration

Edit `settings.yml` to customize your instance:

```yaml
server:
  port: 8888                  # Change port if needed
  bind_address: "127.0.0.1"   # Use "0.0.0.0" for network access (risky!)
  secret_key: "..."           # Auto-generated, keep secure
  limiter: false              # Disable rate limiting for local use

search:
  safe_search: 0              # 0=off, 1=moderate, 2=strict
  default_lang: "auto"

ui:
  default_theme: simple       # Only "simple" theme is available
  theme_args:
    simple_style: auto        # auto, light, dark, black

general:
  instance_name: "SearXNG"
  debug: false                # Set to true for troubleshooting
```

### Available Search Engines (118+ engines enabled)

After a fresh install, SearXNG has 118 engines enabled by default, sourced from the upstream engine list and filtered for Windows compatibility.

| Category | Engines |
|---|---|
| General (77) | Google, DuckDuckGo, Wikipedia, Brave, Bing, Reddit, Imgur, IMDB, Steam, Lemmy, Mastodon, GitHub, Semantic Scholar, and many more |
| Images (3+) | Brave Images, DuckDuckGo Images, Startpage Images, Flickr, Openverse, Pixabay, Artstation, Pexels, Unsplash |
| Videos (2+) | YouTube, Dailymotion, Vimeo, Brave Videos, DuckDuckGo Videos, Odysee, Peertube, Rumble |
| News (3+) | DuckDuckGo News, Startpage News, Bing News, Wikinews, Reuters |
| Science (2) | arXiv, Semantic Scholar, OpenAlex |
| IT (12) | GitHub, PyPI, MDN, Docker Hub, GitLab, npm, StackOverflow, HackerNews, and more |
| Q&A (6) | StackOverflow, AskUbuntu, SuperUser, discuss.python, caddy.community, pi-hole.community |
| Maps (1) | OpenStreetMap |
| Music (1) | Bandcamp, SoundCloud, Mixcloud |
| Dictionaries (2) | Wiktionary, Etymonline, Dictzone |
| Packages (4) | PyPI, Docker Hub, npm, crates.io |
| Wikimedia (2) | Wiktionary, Wikinews, Commons |

See the full list in `searx/searx/settings.yml` (the upstream config).

## MCP (Model Context Protocol)

This package includes a built-in MCP server that wraps SearXNG as Claude Code tools, so AI assistants can search the web without Docker.

### Quick Start (Claude Code)

Add to your Claude Code MCP config (`~/.claude/settings.json`):

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

Or use the convenience script:
```powershell
.\run-mcp.ps1
```

### Available MCP Tools

| Tool | Description |
|---|---|
| `search` | Full-featured search with all parameters |
| `search_quick` | Quick search with defaults |
| `search_images` | Image search |
| `search_videos` | Video search |
| `search_its` | IT/developer resource search |
| `search_academic` | Academic/scientific search |
| `search_engine` | Single-engine search (e.g. Wikipedia) |
| `search_with_time` | Time-filtered search |
| `search_multilang` | Language-specific search |
| `list_engines` | List available search engines |

### Using MCP Tools

Once connected, Claude Code can use tools like:

```
"Search for the latest Python release notes"
→ Claude Code uses search_quick automatically
```

The SearXNG instance must be running (`start.bat`) for the MCP server to work.

## Troubleshooting

### "Python not found"

Make sure Python is in PATH. Open a **new** terminal and type:

```
python --version
```

If it fails, reinstall Python and check **"Add Python to PATH"**.

### "Execution Policy" error

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Static files not loading (no CSS/styling)

This is fixed by the installer automatically. If it still happens:

```powershell
# Re-run the static file fix step
$theme = "searx\searx\static\themes\simple"
$static = "searx\searx\static"
Get-ChildItem $theme -File | Where-Object { $_.Name -like "sxng-*" } |
  ForEach-Object { Copy-Item $_.FullName $static -Force }
if (-not (Test-Path "$static\img")) {
  Copy-Item "$theme\img" "$static\img" -Recurse -Force
}
```

### Search returns errors

Some search engines (Startpage, Brave) may rate-limit you if you make too many
requests too quickly. Wait a few minutes and try again. This is normal.

### Port already in use

Change the port in `settings.yml`:

```yaml
server:
  port: 9999    # or any other port
```

### "TemplateNotFound" error

This happens when the templates path isn't resolved. The installer fixes this
automatically. If it recurs, clear the Python cache:

```powershell
Remove-Item __pycache__, searx\searx\__pycache__ -Recurse -Force
```

## Updating

```powershell
cd searx
git pull
cd ..
pip install -r searx/requirements.txt
```

Or re-run `install.ps1` — it detects existing installations and only updates
what's needed.

## Security Notes

- **Do not** bind to `0.0.0.0` unless you understand the risks
- **Do not** set `public_instance: true` without proper rate limiting
- Keep `settings.yml` secure — it contains the `secret_key`
- The `secret_key` is used to sign cookies and HMAC tokens

## License

SearXNG is licensed under the [AGPL-3.0](https://www.gnu.org/licenses/agpl-3.0.html).

This Windows packaging is released under the same license.
