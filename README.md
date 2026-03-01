# Audio Overview Studio

A local-first web app for generating podcast-style audio from any document, article, or pasted text. Pick your hosts, assign them real voices, choose a format, and get a fully produced audio file — powered by any LLM you already have running.

---

## What It Does

You feed it content. It writes a script between AI hosts, converts that script to audio using your own voice samples, and hands you a downloadable WAV. Every word of every prompt it sends to the LLM is editable in the built-in settings page.

---

## Table of Contents

- [Stack](#stack)
- [Quick Start](#quick-start)
- [Sources — What You Can Feed It](#sources)
- [Podcast Formats](#podcast-formats)
- [Custom Voices](#custom-voices)
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
| Frontend | React 18 + Vite + TypeScript |
| Backend | Python 3.11+ / FastAPI |
| Script generation | Ollama (local), Gemini, Grok, OpenAI |
| Voice synthesis | LuxTTS (XTTS-based, runs locally) |
| Audio stitching | pydub |

---
<img width="2136" height="1218" alt="image" src="https://github.com/user-attachments/assets/fcfbad8e-699f-4e6d-b30a-3e7306933a9f" />

## Quick Start

### First-time setup

```bash
# 1. Backend
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt

# 2. LuxTTS dependencies (adjust path to wherever temp_luxtts lives)
pip install torch torchaudio
pip install -r "../path/to/temp_luxtts/requirements.txt"

# 3. Frontend
cd ../frontend
npm install

# 4. Copy and fill in your keys
cp .env.example ../.env
```

### Every time after that

```bash
python launch.py
```

This starts the backend on port **8001** and the frontend on port **5173** in one terminal. Press `Ctrl+C` to stop both.

Open [http://localhost:5173](http://localhost:5173)

### Manual start (if you prefer separate terminals)

```bash
# Terminal 1 — backend
cd backend
.venv\Scripts\activate
uvicorn main:app --reload --port 8001

# Terminal 2 — frontend
cd frontend
npm run dev
```

---

## Sources

You can combine any number of sources before generating. They are all concatenated into one context block.

| Method | How |
|---|---|
| **Upload file** | PDF, TXT, or Markdown. Text is extracted automatically from PDFs. |
| **Paste text** | Click "Paste text", paste anything, click "Add as source". |
| **Add URL** | Click "Add URL", enter any web address. The backend fetches the page, strips HTML, and adds the extracted text as a source. |

Click the **×** next to any source to remove it before generating.

---

## Podcast Formats

Select a format before generating. Each one changes the structure of the script sent to the LLM.

| Format | Hosts | Description |
|---|---|---|
| **Deep Dive** | 2 | Two hosts have a full discussion — unpacking ideas, making connections, asking questions. Best for most content. |
| **The Brief** | 1 | Single speaker delivers the key takeaways, fast. Under 2 minutes. |
| **The Critique** | 2 | Two hosts give constructive feedback on the material. Good for evaluating documents, proposals, or code. |
| **The Debate** | 2 | Two hosts argue different sides of the ideas in the source. |
| **AI Council Review** | 3 | Gemini, Grok, and OpenAI each take a host role. Round 1: initial analysis. Round 2: debate. Round 3: synthesis. Requires all three cloud API keys. |

### Focus (optional)

Below the format selector there is a **Focus** field. Anything you type there is appended to the LLM prompt as an additional instruction — e.g. *"Emphasize the security implications"* or *"Keep it accessible for a non-technical audience"*.

---

## Custom Voices

Voices are the core of what makes each episode feel different. Every voice is a combination of an **audio sample** (for cloning) and a **character statement** (for the LLM).

### How to add a voice

1. In the **Voices** panel, fill in:
   - **Name** — what it's called in the UI (e.g. `Morgan`)
   - **Character statement** — a description of how this character speaks, behaves, and what they care about
2. Click **Select audio sample (MP3)** and pick a clean MP3 of that voice
3. The voice is saved to `data/custom_voices/` and is immediately available

### Character statements

The character statement is injected directly into the LLM system prompt alongside the script instructions. It shapes how the host speaks, what they focus on, and how they interact with the other host.

**Examples:**

```
A seasoned technology expert with 20 years in software engineering.
Speaks in precise technical terms, loves diving into implementation details,
and pushes back when things are oversimplified.
```

```
Completely non-technical. Has never written a line of code and is proud of it.
Asks "but what does that actually mean for real people?" constantly.
Translates everything into everyday language. Gets genuinely confused by jargon.
```

```
A clueless valley girl who somehow ended up in a tech podcast.
Relates everything back to shopping, drama, or her friends.
Accidentally makes surprisingly insightful observations.
Ends sentences with "like" and "literally" and "oh my god".
```

The character statement is entirely free-form — write whatever you want the model to embody.

### Voice assignment

- **Deep Dive / Critique / Debate**: Assign Host 1 and Host 2
- **The Brief**: Assign Host 1 only
- **AI Council Review**: Assign Host 1 (Gemini), Host 2 (Grok), and Host 3 (OpenAI)

You can assign the same voice to multiple hosts or mix and match freely.

### Voice storage

Voices are saved locally at:

```
data/custom_voices/{voice_id}/
  sample.mp3       ← your audio sample (used by LuxTTS for voice cloning)
  config.json      ← name, character_statement, id
```

The `data/` folder is gitignored — your voices never leave your machine unless you put them there.

---

## LLM Providers

Use the **Provider** toggle at the top to switch between local and cloud.

### Local — Ollama

Runs completely offline. No API keys needed.

1. Install [Ollama](https://ollama.com) and run `ollama serve`
2. Pull a model: `ollama pull llama3.2`
3. Select "Local (Ollama)" in the UI
4. Pick your model from the dropdown (populated live from `ollama list`)

**No timeout** — local generation runs as long as it needs to on slower machines.

### Cloud

| Provider | Key needed | Notes |
|---|---|---|
| **Gemini** | `GEMINI_API_KEY` | Default model: `gemini-2.5-flash` |
| **Grok** | `XAI_API_KEY` | Default model: `grok-3` |
| **OpenAI** | `OPENAI_API_KEY` | Default model: `gpt-4o` |

All three can override their model per-session from the Provider panel dropdown.

### AI Council Review

This format requires all three cloud keys simultaneously. Each provider takes a distinct host role with its own personality (editable in Prompt Settings).

---

## Chat Panel

A live chat interface at the right side of the screen. Use it to talk to one, two, or three AI models at once, or to all three as the AI Council.

### Modes

| Mode | Models active |
|---|---|
| **1 character** | One model, with a custom agent statement and provider you choose |
| **2 characters** | Two models, each with their own provider and agent statement. Their replies appear side by side. |
| **3 characters** | Three models, each independent |
| **AI Council** | Gemini + Grok + OpenAI, each speaking with their council personality (editable in Prompt Settings) |

### Agent statements in chat

In 1/2/3 character modes, each character has an **agent statement** field — the same concept as voice character statements, but for chat. Write any role, personality, or instruction. It's injected as a profile note into that model's system prompt.

Chat is **text only** — no TTS is generated in chat mode.

---

## Prompt Settings

Click the **⚙ Prompts** button in the top-right corner of the header to open the settings panel.

Every string sent to the LLM is editable here. Changes are saved to `data/prompts.json` and take effect on the next generation — no restart needed.

### Sections

**Script Generation**
- `Scriptwriter Role` — The opening identity instruction. Tells the LLM what it is.
- `Output Instructions` — How to label speakers, how long the script should be, what formatting rules to follow.

**Format Instructions**
- One editable field per format: `Deep Dive`, `Brief`, `Critique`, `Debate`. The selected format's instruction is injected into the system prompt at generation time.

**AI Council Review — Round 1 (Analysis)**
- `Council Intro` — The shared context block all three counselors receive before the review starts.
- `Host A / B / C (Analysis)` — What each counselor is instructed to do in the first round.

**AI Council Review — Round 2 (Debate)**
- `Host A / B / C (Debate)` — What each counselor is instructed to do in the second debate round.

**Chat — AI Council Personalities**
- `Gemini / Grok / OpenAI Personality` — The personality injected when those models are used in AI Council chat mode.

**Chat**
- `Chat Base System` — The base instruction appended to every chat conversation, after the conversation history.

### Enhance with AI

Every field has a **✦ Enhance** button. Click it to send the current contents of that field to the first available cloud LLM (Gemini → Grok → OpenAI), along with a meta-prompt asking it to rewrite the prompt to be clearer and more effective. The improved version replaces the field contents — you can edit it further before saving.

### Other controls

- **Blue dot** next to a label means that field has been modified from its default
- **↩ Restore default** appears below any modified field to revert just that one
- **Reset to Defaults** at the top reverts everything and saves
- **Save All** persists all changes to `data/prompts.json`

---

## API Reference

All routes are prefixed with `/api`.

### Sources

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/sources/upload` | Upload a PDF, TXT, or MD file. Returns `source_id`. |
| `POST` | `/api/sources/text` | Add pasted text. Body: `{ "text": "..." }`. Returns `source_id`. |
| `POST` | `/api/sources/url` | Fetch a URL and extract text. Body: `{ "url": "..." }`. Returns `source_id`. |
| `GET` | `/api/sources/{id}/text` | Get the extracted text for a source. |

### Generation

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/generate` | Generate podcast audio. See body schema below. |
| `GET` | `/api/audio/{audio_id}` | Download generated WAV file. |

**`POST /api/generate` body:**
```json
{
  "source_ids": ["abc123"],
  "format": "deep_dive",
  "provider": "local",
  "cloud_provider": "gemini",
  "ollama_model": "llama3.2",
  "gemini_model": "gemini-2.5-flash",
  "host1_voice_id": "abc",
  "host2_voice_id": "def",
  "host3_voice_id": "ghi",
  "custom_prompt": "Focus on the risks"
}
```

### Voices

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/voices` | List all uploaded voices. |
| `POST` | `/api/voices/upload` | Upload a new voice (multipart: `file`, `name`, `character_statement`). |

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

### Status / Diagnostics

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Backend health check. |
| `GET` | `/api/tts-status` | LuxTTS setup diagnostics. |
| `GET` | `/api/llm-status` | LLM availability check. |
| `GET` | `/api/ollama-models` | List installed Ollama models. |

---

## Environment Variables

Copy `.env.example` to `.env` in the project root and fill in what you need.

```env
# LLM — Cloud providers (all optional, use what you have)
GEMINI_API_KEY=
XAI_API_KEY=
OPENAI_API_KEY=

# LLM — Local Ollama
AOS_OLLAMA_HOST=http://localhost:11434
AOS_OLLAMA_MODEL=llama3.2

# Default cloud models (optional overrides)
AOS_GEMINI_MODEL=gemini-2.5-flash
AOS_OPENAI_MODEL=gpt-4o
AOS_GROK_MODEL=grok-3

# LuxTTS path — point this to your temp_luxtts folder
AOS_LUXTTS_PATH=../path/to/temp_luxtts

# Storage (defaults to system temp)
AOS_UPLOAD_DIR=
```

You do not need cloud keys to run the app — Ollama alone is sufficient for all formats except AI Council Review.

---

## Troubleshooting

**LuxTTS not loading**
Visit [http://localhost:8001/api/tts-status](http://localhost:8001/api/tts-status) — it will tell you exactly what is missing (wrong path, missing torch, etc.).

```bash
# If torch is missing from the venv:
cd backend
.venv\Scripts\activate
pip install torch torchaudio
```

**Ollama not available**
Make sure `ollama serve` is running in a separate terminal, or that it started automatically. Check with:
```bash
curl http://localhost:11434/api/tags
```

**AI Council Review fails**
All three keys — `GEMINI_API_KEY`, `XAI_API_KEY`, and `OPENAI_API_KEY` — must be set in `.env`. Check [http://localhost:8001/api/llm-status?format_type=ai_council_review](http://localhost:8001/api/llm-status?format_type=ai_council_review).

**Generation takes a long time**
Normal for local Ollama on consumer hardware. The app has no timeout for local inference — it will wait as long as needed.

**Port conflict on 8001**
Edit `launch.py` and `frontend/vite.config.ts` to change the backend port, then update the proxy target in `vite.config.ts` to match.
