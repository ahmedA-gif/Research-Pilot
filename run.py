#!/usr/bin/env python3
"""ResearchPilot — Frictionless Application Launcher.
Checks environment, starts the server on port 8050, and displays a user-friendly console.
"""

import os
import sys
import time
import socket
import webbrowser
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def kill_process_on_port(port: int):
    try:
        out = subprocess.check_output(["lsof", "-t", f"-i:{port}"]).decode().strip()
        if out:
            pids = out.split()
            for pid in pids:
                subprocess.call(["kill", "-9", pid])
            time.sleep(0.5)
    except Exception:
        pass

def main():
    port = 8050
    print("\n" + "=" * 65)
    print("  🚀  ResearchPilot — Autonomous AI Research Workspace")
    print("=" * 65)
    print(f"Directory: {BASE_DIR}")

    # Check virtual environment python
    venv_python = BASE_DIR / ".venv" / "bin" / "python"
    venv_uvicorn = BASE_DIR / ".venv" / "bin" / "uvicorn"

    if not venv_uvicorn.exists():
        print("❌ Virtual environment not found in .venv. Using system uvicorn...")
        cmd = ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", str(port)]
    else:
        cmd = [str(venv_uvicorn), "backend.main:app", "--host", "0.0.0.0", "--port", str(port)]

    # Free port 8050 if previously occupied by a stale server
    if is_port_in_use(port):
        print(f"ℹ️  Cleaning existing process on port {port}...")
        kill_process_on_port(port)

    url = f"http://localhost:{port}"
    print(f"\n✓ Starting backend server on {url}")
    print(f"✓ Interactive Web Dashboard : {url}")
    print(f"✓ Swagger API Documentation : {url}/docs")
    print(f"✓ Terminal Verification Demo: python3 verify_terminal.py")
    print("\nPress Ctrl+C to stop the server.\n" + "-" * 65 + "\n")

    # Launch browser automatically after 1 second
    try:
        def open_browser():
            time.sleep(1.2)
            webbrowser.open(url)
        import threading
        threading.Thread(target=open_browser, daemon=True).start()
    except Exception:
        pass

    try:
        subprocess.run(cmd, cwd=str(BASE_DIR))
    except KeyboardInterrupt:
        print("\n👋 ResearchPilot server stopped cleanly.")

if __name__ == "__main__":
    main()
