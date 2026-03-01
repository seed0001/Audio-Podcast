"""
API Test Pipeline — staged verification of backend connectivity and chat API.

Run: python scripts/test_api_pipeline.py

Starts a fresh backend process, runs tests, then shuts it down.
"""

import atexit
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT / "backend"
BACKEND_URL = "http://127.0.0.1:8002"  # Pipeline uses 8002 so it doesn't conflict with launch.py (8001)

FAILED = []
PASSED = []
_proc = None


def _start_backend():
    global _proc
    venv_py = BACKEND_DIR / ".venv" / "Scripts" / "python.exe"
    if not venv_py.exists():
        venv_py = BACKEND_DIR / ".venv" / "bin" / "python"
    py = str(venv_py) if venv_py.exists() else sys.executable
    _proc = subprocess.Popen(
        [py, "-m", "uvicorn", "main:app", "--port", "8002"],
        cwd=str(BACKEND_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _stop_backend():
    global _proc
    if _proc and _proc.poll() is None:
        _proc.terminate()
        try:
            _proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _proc.kill()


def stage(name: str, fn):
    """Run a stage; record pass/fail."""
    try:
        fn()
        PASSED.append(name)
        print(f"  [OK] {name}")
        return True
    except Exception as e:
        FAILED.append((name, str(e)))
        print(f"  [FAIL] {name}: {e}")
        return False


def main():
    try:
        import httpx
    except ImportError:
        print("pip install httpx")
        sys.exit(1)

    print("=" * 60)
    print("API Test Pipeline")
    print("=" * 60)
    print("Starting fresh backend on port 8002...")
    _start_backend()
    atexit.register(_stop_backend)
    for _ in range(30):
        try:
            r = httpx.get(f"{BACKEND_URL}/health", timeout=2)
            if r.status_code == 200:
                break
        except Exception:
            time.sleep(0.5)
    else:
        print("Backend failed to start within 15s")
        sys.exit(1)
    print(f"Target: {BACKEND_URL}\n")

    client = httpx.Client(timeout=15.0)

    # Stage 1: Backend reachable
    print("Stage 1: Backend reachable")
    def s1():
        r = client.get(f"{BACKEND_URL}/health")
        r.raise_for_status()
        data = r.json()
        if data.get("status") != "ok":
            raise RuntimeError(f"Unexpected health response: {data}")
    stage("GET /health", s1)
    print()

    # Stage 1b: Verify required routes are registered
    REQUIRED = {"/api/ollama-models", "/api/chat", "/api/voices", "/health"}
    print("Stage 1b: Route registration")
    def routes():
        r = client.get(f"{BACKEND_URL}/openapi.json")
        r.raise_for_status()
        spec = r.json()
        registered = set(spec.get("paths", {}).keys())
        for p in sorted(registered):
            print(f"    {p}")
        missing = [p for p in REQUIRED if p not in registered]
        if missing:
            raise RuntimeError(f"Missing routes: {missing}")
    stage("Required routes registered", routes)
    print()

    # Stage 2: API routes exist
    print("Stage 2: API routes exist")
    def s2a():
        r = client.get(f"{BACKEND_URL}/api/voices")
        r.raise_for_status()
    stage("GET /api/voices", s2a)

    def s2b():
        r = client.get(f"{BACKEND_URL}/api/ollama-models")
        r.raise_for_status()
    stage("GET /api/ollama-models", s2b)
    print()

    # Stage 3: Chat API reachable (POST)
    print("Stage 3: Chat API reachable (POST /api/chat)")
    def s3():
        payload = {
            "mode": "single",
            "messages": [{"role": "user", "content": "Say hi in one word."}],
            "provider": "local",
            "character_providers": ["local"],
            "agent_statements": [],
        }
        r = client.post(f"{BACKEND_URL}/api/chat", json=payload)
        if r.status_code == 404:
            raise RuntimeError("404 Not Found — route /api/chat not registered")
        r.raise_for_status()
    stage("POST /api/chat (local)", s3)
    print()

    # Stage 4: Chat returns valid response
    print("Stage 4: Chat returns valid response")
    def s4():
        payload = {
            "mode": "ai_council",
            "messages": [{"role": "user", "content": "Reply with one word: ok"}],
        }
        r = client.post(f"{BACKEND_URL}/api/chat", json=payload)
        if r.status_code == 404:
            raise RuntimeError("404 Not Found — route /api/chat not registered")
        r.raise_for_status()
        data = r.json()
        if "replies" not in data and "content" not in data:
            raise RuntimeError(f"Invalid response shape: {list(data.keys())}")
    stage("POST /api/chat (ai_council)", s4)
    print()

    client.close()

    # Summary
    print("=" * 60)
    if FAILED:
        print("FAILED stages:")
        for name, err in FAILED:
            print(f"  - {name}: {err}")
        print()
        sys.exit(1)
    else:
        print("All stages passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
