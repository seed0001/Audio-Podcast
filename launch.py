"""
Audio Overview Studio — Launcher.

Starts both backend (FastAPI) and frontend (Vite) in separate subprocesses.
Press Ctrl+C to stop both.
"""

import os
import signal
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"

# Python in backend venv, or current interpreter
VENV_PY = BACKEND_DIR / ".venv" / "Scripts" / "python.exe"
if not VENV_PY.exists():
    VENV_PY = BACKEND_DIR / ".venv" / "bin" / "python"
PYTHON = str(VENV_PY) if VENV_PY.exists() else sys.executable


def main() -> None:
    # Ensure we're in project root
    os.chdir(ROOT)

    # Start backend (port 8001 — avoids conflict with stray process on 8000)
    backend = subprocess.Popen(
        [PYTHON, "-m", "uvicorn", "main:app", "--reload", "--port", "8001"],
        cwd=str(BACKEND_DIR),
        stdout=sys.stdout,
        stderr=sys.stderr,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
    )

    # Start frontend (Vite dev on port 5173, proxies /api to backend)
    npm = "npm.cmd" if sys.platform == "win32" else "npm"
    frontend = subprocess.Popen(
        [npm, "run", "dev"],
        cwd=str(FRONTEND_DIR),
        stdout=sys.stdout,
        stderr=sys.stderr,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
    )

    def cleanup() -> None:
        for proc, name in [(backend, "backend"), (frontend, "frontend")]:
            if proc.poll() is None:
                print(f"\nStopping {name}...")
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

    print("Audio Overview Studio")
    print("  Backend:  http://localhost:8001")
    print("  Frontend: http://localhost:5173")
    print("\nUse http://localhost:5173 for the app. Press Ctrl+C to stop.\n")

    try:
        backend.wait()
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()


if __name__ == "__main__":
    main()
