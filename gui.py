"""
SearXNG Launcher — Vaporwave GUI for Windows.
Launches SearXNG and MCP Server as background processes.
Window is glass-like with a transparent/custom title bar.
"""

import os
import sys

# Auto-re-launch with venv python if running from wrong interpreter
_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui.py")
_VENV_PY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv", "Scripts", "python.exe")
if os.path.isfile(_VENV_PY) and sys.executable != _VENV_PY:
    os.execl(_VENV_PY, _VENV_PY, _SCRIPT)

import subprocess
import threading

import customtkinter as ctk

# ─── Vaporwave Palette ───────────────────────────────────────────────────────
BG = "#0a0014"
CARD = "#130030"
CARD_BORDER = "#2a0055"
PURPLE = "#b829e3"
CYAN = "#00f5d4"
PINK = "#f72585"
YELLOW = "#fee440"
TEXT = "#e0d8ff"
DIM = "#6a6090"
GREEN = "#00ff87"
RED = "#ff3d71"

ROOT = os.path.dirname(os.path.abspath(__file__))
VENV_PY = os.path.join(ROOT, "venv", "Scripts", "python.exe")

# ─── Windows helpers ─────────────────────────────────────────────────────────
def _get_pid_for_cmd(cmd_str):
    """Find a PID whose command line matches cmd_str."""
    # Try wmic first (has full command line)
    for args in [
        ["wmic", "process", "where", "name='python.exe'", "get", "CommandLine,ProcessId"],
        ["powershell", "-NoProfile", "-Command",
         "Get-WmiObject Win32_Process | Where-Object {$_.Name -eq 'python.exe'} |"
         " ForEach-Object { $_.CommandLine + '|' + $_.ProcessId }"],
    ]:
        try:
            out = subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL,
                                          creationflags=subprocess.CREATE_NO_WINDOW)
            for line in out.strip().splitlines():
                if cmd_str in line:
                    # Extract PID (last token after | or space-separated)
                    if "|" in line:
                        parts = line.rsplit("|", 1)
                        try:
                            return int(parts[-1].strip())
                        except ValueError:
                            pass
                    else:
                        parts = line.split()
                        if parts:
                            try:
                                return int(parts[-1])
                            except ValueError:
                                pass
            break  # wmic succeeded (even if no match), don't try powershell
        except Exception:
            continue
    return None


def _kill_pid(pid):
    try:
        subprocess.call(["taskkill", "/PID", str(pid), "/F"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def _is_running(cmd_str):
    return _get_pid_for_cmd(cmd_str) is not None


def _get_python():
    """Find a usable python."""
    if os.path.isfile(VENV_PY):
        return VENV_PY
    return None


# ─── Custom title bar & glass window ─────────────────────────────────────────
class GlassFrame(ctk.CTk):
    """Top-level window with glass effect and no native title bar."""

    def __init__(self, **kw):
        super().__init__()
        # Remove native chrome
        self.overrideredirect(True)

        # Glass transparency
        self.wm_attributes("-alpha", 0.96)

        # Background color for transparentframe trick
        bg = kw.get("fg_color", BG)
        self.configure(fg_color=bg)
        self.wm_attributes("-transparentcolor", bg)

        # Position and size
        w = kw.get("width", 420)
        h = kw.get("height", 440)
        self.geometry(f"{w}x{h}+{self._center_x(w)}+{self._center_y(h)}")

        # Drag support
        self._dragging = False
        self._drag_x = 0
        self._drag_y = 0

    def _center_x(self, w):
        try:
            sw = self.winfo_screenwidth()
            return (sw - w) // 2
        except Exception:
            return 100

    def _center_y(self, h):
        try:
            sh = self.winfo_screenheight()
            return (sh - h) // 2 - 30
        except Exception:
            return 200

    # Drag handling
    def _on_press(self, event):
        self._dragging = True
        self._drag_x = event.x
        self._drag_y = event.y

    def _on_move(self, event):
        if self._dragging:
            x = self.winfo_x() - self._drag_x + event.x
            y = self.winfo_y() - self._drag_y + event.y
            self.geometry(f"+{x}+{y}")

    def _on_release(self, event):
        self._dragging = False

    def bind_drag(self, widget):
        """Make a widget draggable (usually the header bar)."""
        widget.bind("<ButtonPress-1>", self._on_press)
        widget.bind("<B1-Motion>", self._on_move)
        widget.bind("<ButtonRelease-1>", self._on_release)


# ─── Status dot ──────────────────────────────────────────────────────────────
class StatusDot(ctk.CTkLabel):
    def __init__(self, parent, running=False):
        color = GREEN if running else RED
        super().__init__(
            parent, text="\u25cf", font=ctk.CTkFont(size=16, family="Webdings"),
            text_color=color, fg_color="transparent"
        )
        self._running = running

    def set(self, running):
        self._running = running
        self.configure(text_color=GREEN if running else RED)


# ─── Service card ────────────────────────────────────────────────────────────
class ServiceCard(ctk.CTkFrame):
    def __init__(self, parent, title, icon, desc, cmd, running_check, info_callback=None):
        super().__init__(
            parent, fg_color=CARD, corner_radius=16,
            border_width=1, border_color=CARD_BORDER
        )
        self._cmd = cmd
        self._proc = None
        self._pid = None
        self._running = running_check
        self._running_check = running_check
        self._info_callback = info_callback

        # Row 1: icon + title + status
        row1 = ctk.CTkFrame(self, fg_color="transparent")
        row1.pack(fill="x", padx=18, pady=(14, 2))

        ctk.CTkLabel(row1, text=icon, font=ctk.CTkFont(size=22), width=30).pack(side="left")
        ctk.CTkLabel(row1, text=title, font=ctk.CTkFont(size=15, weight="bold"),
                      text_color=TEXT).pack(side="left", padx=(8, 0), expand=True, anchor="w")
        self._dot = StatusDot(row1, running=running_check)
        self._dot.pack(side="right")

        # Description
        ctk.CTkLabel(self, text=desc, font=ctk.CTkFont(size=10),
                      text_color=DIM).pack(pady=(2, 4))

        # Button row
        row2 = ctk.CTkFrame(self, fg_color="transparent")
        row2.pack(fill="x", padx=18, pady=(0, 4))

        btn_text = "Stop" if running_check else "Start"
        btn_color = RED if running_check else GREEN
        self._btn = ctk.CTkButton(
            row2, text=btn_text, width=80, height=28,
            fg_color=btn_color, hover_color="#cc2050" if running_check else "#00cc6a",
            corner_radius=8, font=ctk.CTkFont(size=12, weight="bold"),
            text_color=BG, command=self._toggle
        )
        if running_check:
            self._btn.configure(state="normal")
        self._btn.pack(side="left")

        # Info button (only shown if callback provided)
        if info_callback:
            info_btn = ctk.CTkButton(
                row2, text="ℹ Setup", width=65, height=28,
                fg_color=CARD_BORDER, hover_color="#3a0066",
                corner_radius=8, font=ctk.CTkFont(size=10),
                text_color=TEXT, command=info_callback
            )
            info_btn.pack(side="left", padx=(6, 0))

        # Status
        self._status = ctk.CTkLabel(self, text="Running" if running_check else "",
                                     font=ctk.CTkFont(size=9), text_color=DIM)
        self._status.pack(pady=(0, 8))

    def _log(self, msg):
        self._status.configure(text=msg)

    def _toggle(self):
        if self._running:
            self._stop()
        else:
            self._start()

    def _start(self):
        py = _get_python()
        if not py:
            self._log("venv not found")
            return
        self._log("Starting...")
        self._btn.configure(text="Stop", fg_color=RED, hover_color="#cc2050")
        self._dot.set(True)
        t = threading.Thread(target=self._run, daemon=True)
        t.start()

    def _run(self):
        try:
            kwargs = {
                "cwd": ROOT,
                "creationflags": subprocess.CREATE_NO_WINDOW,
                "stdout": subprocess.DEVNULL,
                "stderr": subprocess.DEVNULL,
            }
            self._proc = subprocess.Popen([_get_python()] + self._cmd, **kwargs)
            self._pid = self._proc.pid
            self._running = True
            self._log(f"Running (PID {self._pid})")
        except Exception as e:
            self._log(f"Error: {e}")
            self._dot.set(False)
            self._btn.configure(text="Start", fg_color=GREEN, hover_color="#00cc6a")

    def _stop(self):
        if self._proc:
            self._log("Stopping...")
            self._proc.terminate()
            try:
                self._proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._proc.kill()
            self._proc = None
            self._running = False
            self._btn.configure(text="Start", fg_color=GREEN, hover_color="#00cc6a")
            self._dot.set(False)
            self._log("Stopped")
        elif self._pid:
            # Process already died but we still have the PID
            _kill_pid(self._pid)
            self._pid = None
            self._running = False
            self._btn.configure(text="Start", fg_color=GREEN, hover_color="#00cc6a")
            self._dot.set(False)
            self._log("Stopped")


# ─── App ─────────────────────────────────────────────────────────────────────
class App(GlassFrame):
    HEADER_H = 36

    def __init__(self):
        super().__init__(width=420, height=440)
        self.title("")  # No native title bar

        # ── Custom header bar ──
        header = ctk.CTkFrame(self, fg_color="#0d0020", height=self.HEADER_H, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        self.bind_drag(header)

        ctk.CTkLabel(header, text="SEARXNG", font=ctk.CTkFont(size=14, weight="bold"),
                      text_color=PURPLE).pack(side="left", padx=14, pady=8)

        # Close button
        close_btn = ctk.CTkButton(header, text="✕", width=30, height=24,
                                   fg_color="transparent", hover_color=RED,
                                   corner_radius=6, font=ctk.CTkFont(size=12),
                                   text_color=TEXT, command=self.destroy)
        close_btn.pack(side="right", padx=14, pady=6)

        # ── Content (below header) ──
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=(8, 0))

        # Check for running processes
        sxng_running = _is_running("wsgi.py")
        mcp_running = _is_running("mcp_server.py")

        self.sxng = ServiceCard(
            body, "SearXNG", "\U0001f52e",
            "Private metasearch — http://127.0.0.1:8888",
            cmd=["wsgi.py"], running_check=sxng_running,
            info_callback=self._show_sxng_info
        )
        self.sxng.pack(fill="x", pady=(0, 10))

        self.mcp = ServiceCard(
            body, "MCP Server", "\u26a1",
            "AI search tools for Claude Code · Click Setup to configure",
            cmd=["mcp_server.py", "--transport", "stdio"], running_check=mcp_running,
            info_callback=self._show_mcp_info
        )
        self.mcp.pack(fill="x")

        # ── Footer ──
        ft = ctk.CTkFrame(self, fg_color="transparent")
        ft.pack(fill="x", pady=(8, 14))
        ctk.CTkLabel(ft, text="Click Start to launch · Services run in background",
                      font=ctk.CTkFont(size=9), text_color=DIM).pack()

        # ── Startup check ──
        self.after(300, self._check)

    def _check(self):
        py = _get_python()
        if not py:
            for card in (self.sxng, self.mcp):
                card._btn.configure(state="disabled")

    def _show_sxng_info(self):
        self._show_info(
            "SearXNG",
            f"""Path: {ROOT}

SearXNG is a free metasearch engine that
aggregates results from various search
services. Users are neither tracked nor
profiled.

Web Interface: http://127.0.0.1:8888

To stop: click the Stop button on the
SearXNG card, or Ctrl+C in the terminal."""
        )

    def _show_mcp_info(self):
        self._show_info(
            "MCP Server Setup",
            f"""The MCP Server wraps SearXNG search as
tools any AI client can use.

Prerequisites:
  • SearXNG must be running first
  • Use the GUI or run: python mcp_server.py
  • Default URL: http://127.0.0.1:8888

Every client needs the same config:

Command:  {VENV_PY}
Arguments: mcp_server.py --transport stdio

───────────────────────────────────────

Claude Code — add to ~/.claude/settings.json:
  {{"mcpServers": {{
    "searxng-search": {{
      "command": "{VENV_PY.replace(chr(92), "/")}",
      "args": ["mcp_server.py", "--transport", "stdio"]
    }}
  }}}}

Cursor — Settings → Features → MCP → Add Server:
  Command: {VENV_PY}
  Args: mcp_server.py --transport stdio

Windsurf — MCP settings, paste command + args:
  Command: {VENV_PY}
  Args: mcp_server.py --transport stdio

Continue (VS Code) — ~/.continue/config.json:
  "mcp": {{
    "searxng-search": {{
      "command": "{VENV_PY.replace(chr(92), "/")}",
      "args": ["mcp_server.py", "--transport", "stdio"],
      "type": "server"
    }}
  }}

───────────────────────────────────────

10 Tools Available:
  search, search_quick, search_images,
  search_videos, search_its, search_academic,
  search_engine, list_engines,
  search_with_time, search_multilang"""
        )

    def _show_info(self, title, text):
        win = ctk.CTkToplevel(self)
        win.title(title)
        win.configure(fg_color=BG)
        win.geometry("400x500")
        win.resizable(True, True)

        # Center on main window
        mx = self.winfo_x() + self.winfo_width() // 2 - 200
        my = self.winfo_y() + self.winfo_height() // 2 - 250
        win.geometry(f"+{mx}+{my}")

        # Header
        hdr = ctk.CTkFrame(win, fg_color="#0d0020", height=40)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text=title, font=ctk.CTkFont(size=14, weight="bold"),
                      text_color=PURPLE).pack(pady=8)

        # Close button
        close = ctk.CTkButton(hdr, text="✕", width=28, height=24,
                               fg_color="transparent", hover_color=RED,
                               corner_radius=6, font=ctk.CTkFont(size=11),
                               text_color=TEXT, command=win.destroy)
        close.pack(side="right", padx=12)

        # Scrollable text area
        txt = ctk.CTkTextbox(win, font=ctk.CTkFont(family="Consolas", size=10),
                              fg_color="#080010", text_color=CYAN,
                              wrap="word", corner_radius=0, border_width=0,
                              padx=12, pady=12)
        txt.pack(fill="both", expand=True)
        txt.insert("1.0", text)
        txt.configure(state="disabled")


if __name__ == "__main__":
    App().mainloop()
