"""
Audio Overview Studio — Launcher.

Starts both backend (FastAPI) and frontend (Vite) in separate subprocesses.
Press Ctrl+C to stop both.
"""

import os
import signal
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"

BACKEND_PORT = 8001
FRONTEND_PORT = 5173

# Python in backend venv, or current interpreter
VENV_PY = BACKEND_DIR / ".venv" / "Scripts" / "python.exe"  # Windows
if not VENV_PY.exists():
    VENV_PY = BACKEND_DIR / ".venv" / "bin" / "python3"      # Mac / Linux (python3)
if not VENV_PY.exists():
    VENV_PY = BACKEND_DIR / ".venv" / "bin" / "python"       # Mac / Linux fallback
PYTHON = str(VENV_PY) if VENV_PY.exists() else sys.executable


def _venv_exists() -> bool:
    return (BACKEND_DIR / ".venv").exists()


def _wait_for_backend(timeout: int = 30) -> bool:
    """Poll until the backend health endpoint responds, or timeout."""
    url = f"http://127.0.0.1:{BACKEND_PORT}/health"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2):
                return True
        except Exception:
            time.sleep(0.5)
    return False


def main() -> None:
    os.chdir(ROOT)

    # --- Pre-flight checks ---
    if not _venv_exists():
        print("\n[ERROR] Python virtual environment not found.")
        print("  Run the setup script first:")
        print("    Mac / Linux:  bash setup.sh")
        print("    Windows:      setup.bat\n")
        sys.exit(1)

    if not (FRONTEND_DIR / "node_modules").exists():
        print("\n[ERROR] Frontend dependencies not installed.")
        print("  Run the setup script first:")
        print("    Mac / Linux:  bash setup.sh")
        print("    Windows:      setup.bat\n")
        sys.exit(1)

    print("\nAudio Overview Studio — starting...\n")

    # --- Start backend ---
    backend = subprocess.Popen(
        [PYTHON, "-m", "uvicorn", "main:app",
         "--host", "127.0.0.1",
         "--port", str(BACKEND_PORT),
         "--reload"],
        cwd=str(BACKEND_DIR),
        stdout=sys.stdout,
        stderr=sys.stderr,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
    )

    # --- Wait for backend to be ready ---
    print(f"Waiting for backend (port {BACKEND_PORT})...")
    if not _wait_for_backend(timeout=30):
        print(f"\n[ERROR] Backend did not start within 30 seconds.")
        print("  Check the output above for Python errors.")
        print("  Common fixes:")
        print("    - Run setup.sh / setup.bat to install missing dependencies")
        print(f"    - Check nothing else is using port {BACKEND_PORT}")
        print(f"    - Run manually: cd backend && source .venv/bin/activate && uvicorn main:app --port {BACKEND_PORT}\n")
        backend.terminate()
        sys.exit(1)

    print(f"  Backend ready  → http://localhost:{BACKEND_PORT}")

    # --- Start frontend ---
    npm = "npm.cmd" if sys.platform == "win32" else "npm"
    frontend = subprocess.Popen(
        [npm, "run", "dev"],
        cwd=str(FRONTEND_DIR),
        stdout=sys.stdout,
        stderr=sys.stderr,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
    )

    print(f"  Frontend ready → http://localhost:{FRONTEND_PORT}")
    print(f"\n  Open http://localhost:{FRONTEND_PORT} in your browser.")
    print("  Press Ctrl+C to stop.\n")

    def cleanup() -> None:
        for proc, name in [(backend, "backend"), (frontend, "frontend")]:
            if proc.poll() is None:
                print(f"Stopping {name}...")
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()

    def on_signal(*args: object) -> None:
        cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, on_signal)
    signal.signal(signal.SIGTERM, on_signal)

    try:
        backend.wait()
        # If backend exits on its own something went wrong
        if backend.returncode != 0:
            print(f"\n[ERROR] Backend exited unexpectedly (code {backend.returncode}).")
            print("  Check the output above for the error.\n")
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()


if __name__ == "__main__":
    main()
