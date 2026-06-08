#!/usr/bin/env bash
# Audio Overview Studio — Mac / Linux setup script
# Run once: bash setup.sh

set -e

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   Audio Overview Studio — Setup          ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# --- Detect Python ---
PYTHON=""
for cmd in python3 python3.12 python3.11 python3.10 python; do
  if command -v "$cmd" &>/dev/null; then
    VER=$("$cmd" -c "import sys; print(sys.version_info >= (3,11))" 2>/dev/null)
    if [ "$VER" = "True" ]; then
      PYTHON="$cmd"
      break
    fi
  fi
done

if [ -z "$PYTHON" ]; then
  echo "✘ Python 3.11+ not found."
  echo "  Install it from https://python.org/downloads or via Homebrew: brew install python@3.12"
  exit 1
fi

echo "✔ Using Python: $($PYTHON --version)"

# --- .env ---
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "✔ Created .env from .env.example"
  echo "  → You can enter API keys in the app's TTS Setup panel instead of editing .env manually"
else
  echo "✔ .env already exists — skipping"
fi

# --- Python venv ---
echo ""
echo "Setting up Python backend..."
cd backend

if [ ! -d ".venv" ]; then
  "$PYTHON" -m venv .venv
  echo "✔ Created Python virtual environment"
fi

source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "✔ Python dependencies installed"

# --- Kokoro (local TTS, optional but recommended) ---
echo ""
echo "Installing Kokoro TTS (local, no API key needed)..."
pip install "kokoro[en]" -q \
  && echo "✔ Kokoro installed" \
  || echo "⚠ Kokoro install failed — you can use OpenAI or ElevenLabs TTS instead"

cd ..

# --- Node / frontend ---
echo ""
echo "Setting up frontend..."

if ! command -v node &>/dev/null; then
  echo "✘ Node.js not found."
  echo "  Install it from https://nodejs.org (LTS version) or via Homebrew: brew install node"
  exit 1
fi

echo "✔ Using Node: $(node --version)"

cd frontend
npm install -q
echo "✔ Frontend dependencies installed"

cd ..

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   Setup complete!                        ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. Start the app:   python3 launch.py"
echo "  2. Open:            http://localhost:5173"
echo "  3. Click 🎙 TTS Setup to configure your voice engine"
echo "     (enter API keys directly in the UI — no .env editing needed)"
echo ""
