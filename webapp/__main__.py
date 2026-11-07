"""Start the web interface: python -m webapp [--port N] [--no-browser]."""
from __future__ import annotations

import argparse
import os
import sys
import threading
import webbrowser

import uvicorn


def main() -> int:
    if sys.version_info < (3, 10):
        print("Python 3.10+ required", file=sys.stderr)
        return 2
    ap = argparse.ArgumentParser(description="Databricks cost audit - web interface")
    ap.add_argument("--port", type=int, default=int(os.getenv("AUDIT_UI_PORT", "8765")))
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args()
    url = f"http://127.0.0.1:{args.port}/"
    print(f"Databricks cost audit: {url}  (Ctrl+C to stop)")
    if not args.no_browser:
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    uvicorn.run("webapp.main:app", host="127.0.0.1", port=args.port, log_level="warning")
    return 0


if __name__ == "__main__":
    sys.exit(main())
