# Audio Overview Studio

A local-first web app for generating podcast-style audio from any document, article, or pasted text. Pick your hosts, assign them voices, choose a format, and get a fully produced audio file — powered by any LLM you already have running.

<img width="1399" height="872" alt="image" src="https://github.com/user-attachments/assets/f6d4385d-e012-4485-a8e0-d79409a9c205" />
<img width="696" height="864" alt="image" src="https://github.com/user-attachments/assets/c169a758-8630-4e5a-a636-6dcbb4e718ba" />
<img width="2097" height="423" alt="image" src="https://github.com/user-attachments/assets/ddb6e0b4-1618-4584-871d-5078e0421434" />

---

## What It Does

You feed it content. It writes a script between AI hosts, converts that script to audio using your chosen TTS engine, and hands you a downloadable WAV. Every word of every prompt it sends to the LLM is editable in the built-in settings page.

---

## Table of Contents

- [Stack](#stack)
- [Quick Start](#quick-start)
- [TTS Providers](#tts-providers)
- [Sources](#sources)
- [Podcast Formats](#podcast-formats)
- [Voices](#voices)
- [LLM Providers](#llm-providers)
- [Chat Panel](#chat-panel)
- [Prompt Settings](#prompt-settings)
- [API Reference](#api-reference)
- [Environment Variables](#environment-variables)
- [Troubleshooting](#troubleshooting)

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | React 19 + Vite + TypeScript |
| Backend | Python 3.11+ / FastAPI |
| Script generation | Ollama (local), Gemini, Grok, OpenAI |
| Voice synthesis | OpenAI TTS, ElevenLabs, Kokoro (local), LuxTTS |
| Audio stitching | pydub |

---

## Quick Start

### Prerequisites

- **Python 3.11+** — [python.org](https://www.python.org/downloads/)
- **Node.js 18+** — [nodejs.org](https://nodejs.org) (LTS version recommended)
- **Git**

### One-command setup

**Mac / Linux:**
```bash
git clone https://github.com/seed0001/Audio-Podcast
cd Audio-Podcast
bash setup.sh
```

**Windows:**
```bat
git clone https://github.com/seed0001/Audio-Podcast
cd Audio-Podcast
setup.bat
```

The setup script will:
- Create the Python virtual environment
- Install all backend dependencies
- Install Kokoro (local TTS engine — no API key needed)
- Install frontend dependencies
- Create your `.env` file from the template

### Start the app

```bash
python launch.py
```

This starts the backend on port **8001** and the frontend on port **5173** in one terminal. Press `Ctrl+C` to stop both.

Open [http://localhost:5173](http://localhost:5173)

### Configure TTS

Click **🎙 TTS Setup** in the top-right corner of the app to configure your voice engine. See [TTS Providers](#tts-providers) below for what each option requires.

### Manual start (separate terminals)

```bash
# Terminal 1 — backend
cd backend
source .venv/bin/activate      # Mac / Linux
# .venv\Scripts\activate       # Windows
uvicorn main:app --reload --port 8001

# Terminal 2 — frontend
cd frontend
npm run dev
```

---

## TTS Providers

TTS is the core of every podcast. The app supports four providers — configure them in the **🎙 TTS Setup** panel inside the app without touching any config files.

### OpenAI TTS *(recommended for most users)*

High-quality cloud voices. Six built-in voices with no setup beyond an API key.

| | |
|---|---|
| **Requires** | `OPENAI_API_KEY` |
| **Voices** | Alloy, Echo, Fable, Onyx, Nova, Shimmer |
| **Models** | `tts-1` (fast) · `tts-1-hd` (highest quality, recommended) |
| **Install** | Nothing extra — uses your existing OpenAI key |

Get an API key at [platform.openai.com/api-keys](https://platform.openai.com/api-keys).

---

### ElevenLabs *(best podcast quality)*

Studio-grade voices. Free tier includes 10,000 characters per month.

| | |
|---|---|
| **Requires** | `ELEVENLABS_API_KEY` |
| **Voices** | Rachel, Domi, Bella, Antoni, Josh, Arnold, Adam, Sam (+ more) |
| **Models** | Turbo v2.5 · Multilingual v2 · Turbo v2 |
| **Install** | Nothing extra |

Get an API key at [elevenlabs.io](https://elevenlabs.io) → Profile → API Keys.

---

### Kokoro *(local, no API key needed)*

Runs entirely on your machine. No internet required after install. Good quality across US and British English accents.

| | |
|---|---|
| **Requires** | Nothing (no API key, no account) |
| **Voices** | 11 voices — US & British English, male & female |
| **Install — Mac / Linux** | `pip install kokoro[en]` |
| **Install — Windows** | `pip install kokoro[en] misaki[en]` |

The setup script installs Kokoro automatically. First generation may take a moment while the model loads into memory.

---

### LuxTTS *(advanced — voice cloning)*

Clone a voice from your own MP3 sample. Requires a separate repo install and a GPU is strongly recommended.

| | |
|---|---|
| **Requires** | Local clone of the LuxTTS repo + `torch` + `torchaudio` |
| **Voices** | Your own uploaded MP3 samples |
| **Install** | See [LuxTTS setup](#luxtts-setup) below |

#### LuxTTS setup

1. Clone the LuxTTS repo somewhere on your machine
2. Install its dependencies: `pip install torch torchaudio` then `pip install -r /path/to/temp_luxtts/requirements.txt`
3. In **🎙 TTS Setup**, enter the path to your `temp_luxtts` folder — or set `AOS_LUXTTS_PATH` in `.env`
4. Upload voice samples (MP3) in the **Voices** panel

---

## Sources

Combine any number of sources before generating. They are all concatenated into one context block for the LLM.

| Method | How |
|---|---|
| **Upload file** | PDF, TXT, or Markdown. Text is extracted automatically from PDFs. |
| **Paste text** | Click "Paste text", paste anything, click "Add as source". |
| **Add URL** | Click "Add URL", enter any web address. The backend fetches and strips the HTML. |

Click **×** next to any source to remove it before generating.

---

## Podcast Formats

| Format | Hosts | Description |
|---|---|---|
| **Deep Dive** | 2 | Two hosts have a full discussion — unpacking ideas, making connections, asking questions. Best for most content. |
| **The Brief** | 1 | Single speaker delivers the key takeaways fast. |
| **The Critique** | 2 | Two hosts give constructive feedback on the material. Good for evaluating documents, proposals, or code. |
| **The Debate** | 2 | Two hosts argue different sides of the ideas in the source. |
| **AI Council Review** | 3 | Gemini, Grok, and OpenAI each take a host role. Round 1: analysis. Round 2: debate. Requires all three cloud API keys. |

### Focus (optional)

The **Focus** field below the format selector appends an extra instruction to the LLM prompt — e.g. *"Emphasize the security implications"* or *"Keep it accessible for a non-technical audience"*.

---

## Voices

### How voices work

The **Voices** panel shows all voices available from your active TTS provider. For cloud providers (OpenAI, ElevenLabs, Kokoro), built-in voices appear automatically once the provider is configured — no uploads needed.

### Built-in voices

Once you configure a provider in **🎙 TTS Setup**, its voices populate the Voices panel automatically. Select Host 1, Host 2, and Host 3 from the dropdowns.

### Character statements

Every voice can have a **character statement** — a description of how that host speaks, thinks, and behaves. This is injected directly into the LLM prompt and shapes the script writing.

**Examples:**

```
A seasoned technology expert with 20 years in software engineering.
Speaks in precise technical terms, loves diving into implementation details,
and pushes back when things are oversimplified.
```

```
Completely non-technical. Has never written a line of code and is proud of it.
Asks "but what does that actually mean for real people?" constantly.
Translates everything into everyday language.
```

```
A clueless valley girl who somehow ended up in a tech podcast.
Relates everything back to shopping, drama, or her friends.
Accidentally makes surprisingly insightful observations.
```

Character statements are free-form — write whatever you want the model to embody.

### Voice assignment

- **Deep Dive / Critique / Debate**: Host 1 and Host 2
- **The Brief**: Host 1 only
- **AI Council Review**: Host 1 (Gemini), Host 2 (Grok), Host 3 (OpenAI)

### Custom voice uploads (LuxTTS only)

When LuxTTS is the active provider, an upload form appears in the Voices panel:

1. Enter a **Name** and optionally a **Character statement**
2. Click **Select audio sample (MP3)** and pick a clean recording
3. The voice is saved to `data/custom_voices/` and available immediately

Uploaded voices are stored locally at:
```
data/custom_voices/{voice_id}/
  sample.mp3     ← your audio sample
  config.json    ← name, character_statement, id
```

The `data/` folder is gitignored — your voices never leave your machine.

---

## LLM Providers

Use the **Provider** toggle at the top of the app to switch between local and cloud.

### Local — Ollama

Runs completely offline. No API keys needed.

1. Install [Ollama](https://ollama.com) and run `ollama serve`
2. Pull a model: `ollama pull llama3.2`
3. Select "Local (Ollama)" in the UI
4. Pick your model from the dropdown

### Cloud

| Provider | Key | Default model |
|---|---|---|
| **Gemini** | `GEMINI_API_KEY` | `gemini-2.5-flash` |
| **Grok** | `XAI_API_KEY` | `grok-3` |
| **OpenAI** | `OPENAI_API_KEY` | `gpt-4o` |

All three can override their model per-session from the Provider panel dropdown.

### AI Council Review

Requires all three cloud keys simultaneously. Each provider takes a distinct host role with its own personality (editable in Prompt Settings).

---

## Chat Panel

A live chat interface at the right side of the screen. Talk to one, two, or three AI models at once, or all three as the AI Council. Text only — no TTS in chat mode.

| Mode | Models |
|---|---|
| **1 character** | One model with a custom agent statement |
| **2 characters** | Two models, replies appear side by side |
| **3 characters** | Three independent models |
| **AI Council** | Gemini + Grok + OpenAI with council personalities |

**Agent statements** — In 1/2/3 character modes, each character has an agent statement field. Write any role, personality, or instruction.

---

## Prompt Settings

Click **⚙ Prompts** in the header to open the settings panel. Every string sent to the LLM is editable here. Changes are saved to `data/prompts.json` and take effect on the next generation — no restart needed.

- **Blue dot** = field modified from default
- **↩ Restore default** = revert that one field
- **✦ Enhance** = send the field to an AI for rewriting
- **Reset to Defaults** = revert everything
- **Save All** = persist changes

---

## API Reference

All routes are prefixed with `/api`.

### Sources

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/sources/upload` | Upload PDF, TXT, or MD. Returns `source_id`. |
| `POST` | `/api/sources/text` | Add pasted text. Body: `{ "text": "..." }`. |
| `POST` | `/api/sources/url` | Fetch a URL and extract text. Body: `{ "url": "..." }`. |
| `GET` | `/api/sources/{id}/text` | Get extracted text for a source. |

### Generation

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/generate` | Generate podcast audio. |
| `GET` | `/api/audio/{audio_id}` | Download generated WAV. |

**`POST /api/generate` body:**
```json
{
  "source_ids": ["abc123"],
  "format": "deep_dive",
  "provider": "local",
  "cloud_provider": "gemini",
  "ollama_model": "llama3.2",
  "host1_voice_id": "openai:nova",
  "host2_voice_id": "openai:onyx",
  "host3_voice_id": "openai:alloy",
  "custom_prompt": "Focus on the risks"
}
```

Voice IDs follow the format `provider:voice_key` — e.g. `openai:nova`, `elevenlabs:21m00Tcm4TlvDq8ikWAM`, `kokoro:af_heart`.

### Voices

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/voices` | List voices from active provider + custom uploads. |
| `POST` | `/api/voices/upload` | Upload a custom voice MP3 (LuxTTS only). Multipart: `file`, `name`, `character_statement`. |

### TTS Configuration

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/tts-config` | Get current TTS config and provider status. |
| `PUT` | `/api/tts-config` | Save TTS config (active provider, API keys, model). |
| `POST` | `/api/tts-test` | Generate a test audio clip. Body: `{ "voice_id": "openai:nova" }`. |
| `GET` | `/api/tts-status` | Detailed status of all TTS providers. |

### Prompts

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/prompts` | Get current prompts and defaults. |
| `PUT` | `/api/prompts` | Save prompt overrides. Body: `{ "prompts": { "key": "value" } }`. |
| `POST` | `/api/prompts/reset` | Revert all prompts to defaults. |
| `POST` | `/api/prompts/enhance` | Improve a prompt with AI. Body: `{ "text": "...", "context": "..." }`. |

### Chat

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/chat` | Chat with one or multiple models. |

### Status

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Backend health check. |
| `GET` | `/api/llm-status` | LLM availability check. |
| `GET` | `/api/ollama-models` | List installed Ollama models. |

---

## Environment Variables

Copy `.env.example` to `.env` in the project root. Most settings can also be configured directly in the app's **🎙 TTS Setup** panel — no manual file editing required.

```env
# TTS provider (optional — can be set in TTS Setup UI instead)
# Options: openai | elevenlabs | kokoro | luxtts
AOS_TTS_PROVIDER=openai

# OpenAI (TTS + LLM)
OPENAI_API_KEY=

# ElevenLabs (TTS)
ELEVENLABS_API_KEY=

# Gemini (LLM)
GEMINI_API_KEY=

# Grok / xAI (LLM)
XAI_API_KEY=

# Local Ollama
AOS_OLLAMA_HOST=http://localhost:11434
AOS_OLLAMA_MODEL=llama3.2

# Default cloud models (optional overrides)
AOS_GEMINI_MODEL=gemini-2.5-flash
AOS_OPENAI_MODEL=gpt-4o
AOS_GROK_MODEL=grok-3

# LuxTTS path (only needed if using LuxTTS provider)
AOS_LUXTTS_PATH=/path/to/temp_luxtts

# Storage (defaults to system temp directory)
AOS_UPLOAD_DIR=
```

You do not need any cloud keys to run the app. Kokoro (local TTS) + Ollama (local LLM) gives you a fully offline setup.

---

## Troubleshooting

**"Connection refused" / ERR_CONNECTION_REFUSED (Mac errno 61)**
The frontend can't reach the backend. The backend either crashed on startup or hasn't finished loading yet.

1. Check the terminal output for a Python error — a missing package is the most common cause
2. Make sure you ran `bash setup.sh` before `python3 launch.py`
3. If you see `ModuleNotFoundError`, activate the venv and install the missing package:
   ```bash
   cd backend
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
4. Try starting the backend manually to see the full error:
   ```bash
   cd backend
   source .venv/bin/activate
   uvicorn main:app --port 8001
   ```
5. Visit [http://localhost:8001/health](http://localhost:8001/health) — if it loads, the backend is fine and the issue is the frontend proxy

---

**TTS not working**
Open [http://localhost:8001/api/tts-status](http://localhost:8001/api/tts-status) — it shows the status of every provider with a specific error message. Or click **🎙 TTS Setup** in the app to see status indicators directly.

**Kokoro not available after install**
Restart the backend server after installing Kokoro — the import is checked at startup.

```bash
# Windows (in backend venv)
pip install kokoro[en] misaki[en]

# Mac / Linux
pip install kokoro[en]
```

**OpenAI / ElevenLabs key not recognized**
Keys entered in the TTS Setup panel are saved to `data/tts_config.json`. Keys in `.env` always take precedence. If you recently changed a key in `.env`, restart the backend.

**Ollama not available**
Make sure `ollama serve` is running. Check with:
```bash
curl http://localhost:11434/api/tags
```

**AI Council Review fails**
All three keys — `GEMINI_API_KEY`, `XAI_API_KEY`, and `OPENAI_API_KEY` — must be set. Check [http://localhost:8001/api/llm-status?format_type=ai_council_review](http://localhost:8001/api/llm-status?format_type=ai_council_review).

**Generation takes a long time**
Normal for local Ollama on consumer hardware. The app has no timeout for local inference — it will wait as long as needed. Cloud providers are much faster.

**Port conflict on 8001**
Edit `launch.py` and `frontend/vite.config.ts` to change the backend port, then update the proxy target in `vite.config.ts` to match.

**`python launch.py` doesn't open the browser automatically**
Open [http://localhost:5173](http://localhost:5173) manually.
