"""
SearXNG WSGI entry point for Windows (via waitress).
Run with: python wsgi.py
Or:       waitress-serve --port=8888 --listen=127.0.0.1:8888 wsgi:application
"""
import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Add searx/ subdirectory (where the searx Python package lives)
searx_src = os.path.join(project_root, 'searx')
if os.path.isdir(searx_src) and searx_src not in sys.path:
    sys.path.insert(0, searx_src)

# Set settings path so searx finds our config
os.environ['SEARXNG_SETTINGS_PATH'] = os.path.join(project_root, 'settings.yml')

from searx.webapp import app
application = app

if __name__ == '__main__':
    from waitress import serve
    print("[*] Starting SearXNG on http://127.0.0.1:8888")
    print("[*] Press Ctrl+C to stop")
    try:
        serve(
            application,
            host='127.0.0.1',
            port=8888,
            channel_timeout=120,
            cleanup_interval=30,
            _quiet=True
        )
    except KeyboardInterrupt:
        print("\n[*] Shutting down...")
