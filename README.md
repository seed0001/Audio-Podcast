# Audio Overview Studio

A web platform for creating podcast-style audio summaries from your documents — inspired by NotebookLM's Audio Overview, with custom voice selection and upload.

## Stack

- **Frontend:** React 18 + Vite + TypeScript
- **Backend:** Python FastAPI (document ingestion, LLM script generation, TTS)
- **Voices:** LuxTTS / XTTS (local), optional cloud APIs

## Quick Start

### One command (launcher)

```bash
# First time: set up backend + frontend
cd backend && python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt
cd ../frontend && npm install

# Launch both
cd .. && python launch.py
```

Opens backend at http://localhost:8000 and frontend at http://localhost:5173. Press Ctrl+C to stop both.

### Manual

**Backend (Python):**
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend (React):**
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Features

- Upload PDFs, paste text, add URLs
- Generate AI conversation scripts (Deep Dive, Brief, Critique, Debate) via Ollama
- **LuxTTS** for voice generation (uses Adam GURU's temp_luxtts)
- Select or upload custom MP3 voices for each host
- Preview and export podcast-style audio

## Requirements

- **LLM** for script generation. Choose one:
  - **Ollama** (default): Run `ollama serve`, use `llama3.2` or set `AOS_OLLAMA_MODEL`
  - **Gemini**: Set `GEMINI_API_KEY` and `AOS_LLM_PROVIDER=gemini`
- **LuxTTS** at `../New folder (33)/Adam GURU/temp_luxtts` (override with `AOS_LUXTTS_PATH` env var)
- **PyTorch** and LuxTTS deps in the backend venv:
  ```bash
  cd backend
  .venv\Scripts\activate
  pip install torch torchaudio
  pip install -r "../New folder (33)/Adam GURU/temp_luxtts/requirements.txt"
  ```
  Or if temp_luxtts is elsewhere: `pip install -r /path/to/temp_luxtts/requirements.txt`

**Troubleshooting:** Visit `http://localhost:8000/api/tts-status` to see why LuxTTS isn't loading (missing torch, path, etc.).
