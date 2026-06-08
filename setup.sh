#!/usr/bin/env bash
# Audio Overview Studio — Mac / Linux setup script
# Run once: bash setup.sh

set -e

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   Audio Overview Studio — Setup          ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# --- .env ---
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "✔ Created .env from .env.example"
  echo "  → Open .env and add your API keys (or use the TTS Setup panel in the app)"
else
  echo "✔ .env already exists — skipping"
fi

# --- Python venv ---
echo ""
echo "Setting up Python backend..."
cd backend

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  echo "✔ Created Python virtual environment"
fi

source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "✔ Python dependencies installed"

# --- Kokoro (local TTS, optional but recommended) ---
echo ""
echo "Installing Kokoro TTS (local, no API key needed)..."
pip install "kokoro[en]" -q && echo "✔ Kokoro installed" || echo "⚠ Kokoro install failed — you can skip this and use OpenAI or ElevenLabs TTS instead"

cd ..

# --- Node / frontend ---
echo ""
echo "Setting up frontend..."
cd frontend

if ! command -v node &> /dev/null; then
  echo "✘ Node.js not found. Install it from https://nodejs.org (LTS version recommended)"
  exit 1
fi

npm install -q
echo "✔ Frontend dependencies installed"

cd ..

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   Setup complete!                        ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your API key(s)  — OR —"
echo "     enter them in the app's TTS Setup panel"
echo "  2. Start the app: python launch.py"
echo "  3. Open http://localhost:5173"
echo "  4. Click '🎙 TTS Setup' to configure your voice engine"
echo ""
