"""
Audio Overview Studio — FastAPI backend.

Handles source ingestion, LLM conversation generation, and TTS orchestration.
"""

from pathlib import Path
_dotenv = Path(__file__).resolve().parent.parent / ".env"
if _dotenv.exists():
    from dotenv import load_dotenv
    load_dotenv(_dotenv)

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import os
import tempfile
from pathlib import Path

app = FastAPI(title="Audio Overview Studio")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

UPLOAD_DIR = Path(os.getenv("AOS_UPLOAD_DIR", tempfile.gettempdir())) / "aos_uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Voices: user uploads only, saved in project data dir
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
CUSTOM_VOICES_DIR = WORKSPACE_ROOT / "data" / "custom_voices"
CUSTOM_VOICES_DIR.mkdir(parents=True, exist_ok=True)

# Max MP3 size (20 MB)
MAX_VOICE_SIZE = 20 * 1024 * 1024


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class SourceText(BaseModel):
    text: str


class SourceUrl(BaseModel):
    url: str


class PromptsUpdate(BaseModel):
    prompts: dict


class EnhanceRequest(BaseModel):
    text: str
    context: str = ""  # human description of what this prompt does


class GenerateRequest(BaseModel):
    source_ids: list[str]
    format: str = "deep_dive"  # deep_dive | brief | critique | debate | ai_council_review
    provider: str = "local"  # local | cloud
    cloud_provider: Optional[str] = None  # gemini | grok | openai (when provider=cloud)
    ollama_model: Optional[str] = None
    gemini_model: Optional[str] = None
    grok_model: Optional[str] = None
    openai_model: Optional[str] = None
    host1_voice_id: str
    host2_voice_id: Optional[str] = None
    host3_voice_id: Optional[str] = None  # for ai_council_review
    custom_prompt: Optional[str] = None


class VoiceInfo(BaseModel):
    id: str
    name: str
    character_statement: str = ""


class ChatRequest(BaseModel):
    mode: str = "single"  # single | dual | triple | ai_council
    messages: list[dict] = []
    provider: str = "local"
    cloud_provider: Optional[str] = None
    chat_providers: Optional[list[str]] = None
    character_providers: Optional[list[str]] = None  # per-char: "local" | "gemini" | "grok" | "openai"
    agent_statements: Optional[list[str]] = None  # per-char profile/agent statement
    ollama_model: Optional[str] = None
    gemini_model: Optional[str] = None
    grok_model: Optional[str] = None
    openai_model: Optional[str] = None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Prompt settings
# ---------------------------------------------------------------------------

@app.get("/api/prompts")
def get_prompts():
    """Return current prompts and defaults for the settings page."""
    from prompt_store import load_prompts, DEFAULT_PROMPTS
    return {"prompts": load_prompts(), "defaults": dict(DEFAULT_PROMPTS)}


@app.put("/api/prompts")
def update_prompts(body: PromptsUpdate):
    """Save prompt overrides."""
    from prompt_store import save_prompts
    save_prompts({k: str(v) for k, v in (body.prompts or {}).items()})
    return {"status": "saved"}


@app.post("/api/prompts/reset")
def reset_prompts_endpoint():
    """Revert all prompts to defaults."""
    from prompt_store import reset_prompts, load_prompts, DEFAULT_PROMPTS
    reset_prompts()
    return {"prompts": load_prompts(), "defaults": dict(DEFAULT_PROMPTS)}


@app.post("/api/prompts/enhance")
async def enhance_prompt_endpoint(body: EnhanceRequest):
    """Use a cloud LLM to improve a prompt. Auto-selects first available provider."""
    text = (body.text or "").strip()
    if not text:
        raise HTTPException(400, "text is required")

    context_hint = f" This prompt is used for: {body.context.strip()}." if body.context.strip() else ""

    system = (
        "You are an expert prompt engineer. Rewrite the following prompt to be clearer, "
        "more specific, and more effective at guiding an LLM toward the intended output."
        + context_hint
        + " Preserve the original intent exactly. Return ONLY the improved prompt text — "
        "no commentary, no quotes, no explanation."
    )
    user = f"Original prompt:\n\n{text}\n\nImproved prompt:"

    gemini_key = os.getenv("GEMINI_API_KEY")
    xai_key = os.getenv("XAI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    from llm_service import _generate_gemini, _generate_grok, _generate_openai
    from llm_service import GEMINI_MODEL, GROK_MODEL, OPENAI_MODEL

    if gemini_key:
        try:
            result = await _generate_gemini(system, user, 60.0, model=GEMINI_MODEL)
            return {"enhanced": result}
        except Exception:
            pass
    if xai_key:
        try:
            result = await _generate_grok(system, user, 60.0, model=GROK_MODEL)
            return {"enhanced": result}
        except Exception:
            pass
    if openai_key:
        try:
            result = await _generate_openai(system, user, 60.0, model=OPENAI_MODEL)
            return {"enhanced": result}
        except Exception:
            pass

    raise HTTPException(503, "No cloud API key available for enhancement (need GEMINI_API_KEY, XAI_API_KEY, or OPENAI_API_KEY)")


@app.get("/api/ollama-models")
def ollama_models():
    """List Ollama models from local ollama list / api/tags."""
    import httpx
    host = os.getenv("AOS_OLLAMA_HOST", "http://localhost:11434")
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(f"{host.rstrip('/')}/api/tags")
            if r.status_code != 200:
                return {"models": [], "error": r.text or "Ollama unavailable"}
            data = r.json()
            models_raw = data.get("models") or []
            # Use 'name' field (e.g. llama3.2:latest) or 'model'
            names = sorted({m.get("name") or m.get("model", "") for m in models_raw if m.get("name") or m.get("model")})
            return {"models": [n for n in names if n]}
    except Exception as e:
        return {"models": [], "error": str(e)}


@app.get("/api/tts-status")
def tts_status():
    """Diagnostic endpoint for LuxTTS setup."""
    from luxtts_service import get_tts_status
    return get_tts_status()


@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    """Chat with one or more models. No voice — text only."""
    from llm_service import chat, get_llm_status
    mode = (req.mode or "single").lower()
    provider = (req.provider or "local").lower()
    cloud_provider = (req.cloud_provider or "gemini").lower() if req.cloud_provider else None
    chat_providers = req.chat_providers or []

    if mode == "single" and provider == "local":
        st = get_llm_status(provider="local")
        if not st.get("available"):
            raise HTTPException(503, st.get("error") or "Ollama not available.")
    elif mode == "single" and provider == "cloud":
        st = get_llm_status(provider="cloud", cloud_provider=cloud_provider)
        if not st.get("available"):
            raise HTTPException(503, st.get("error") or "Cloud provider not available.")
    elif mode in ("dual", "triple", "ai_council"):
        providers_to_check = req.character_providers if mode in ("dual", "triple") else ["gemini", "grok", "openai"]
        for p in (providers_to_check or ["gemini", "grok", "openai"]):
            if p == "local":
                st = get_llm_status(provider="local")
            else:
                st = get_llm_status(provider="cloud", cloud_provider=p)
            if not st.get("available"):
                raise HTTPException(503, f"{p}: {st.get('error', 'Not available')}")

    models = {
        "ollama": req.ollama_model,
        "gemini": req.gemini_model,
        "grok": req.grok_model,
        "openai": req.openai_model,
    }
    result = await chat(
        mode=mode,
        messages=req.messages,
        provider=provider,
        cloud_provider=cloud_provider,
        chat_providers=chat_providers,
        character_providers=req.character_providers,
        agent_statements=req.agent_statements,
        models=models,
    )
    return result


@app.get("/api/llm-status")
def llm_status(provider: str = "local", cloud_provider: Optional[str] = None, format_type: Optional[str] = None):
    """Diagnostic endpoint for LLM setup."""
    from llm_service import get_llm_status
    return get_llm_status(provider=provider, cloud_provider=cloud_provider, format_type=format_type)


def _load_voices() -> list[VoiceInfo]:
    """Load all voices from data/custom_voices. User uploads only."""
    voices: list[VoiceInfo] = []
    if not CUSTOM_VOICES_DIR.exists():
        return voices
    import json
    for d in CUSTOM_VOICES_DIR.iterdir():
        if d.is_dir():
            config = d / "config.json"
            sample = d / "sample.mp3"
            if sample.exists() and config.exists():
                try:
                    cfg = json.loads(config.read_text(encoding="utf-8"))
                    voices.append(VoiceInfo(
                        id=cfg.get("id", d.name),
                        name=cfg.get("name", d.name),
                        character_statement=cfg.get("character_statement", ""),
                    ))
                except Exception:
                    pass
    return voices


@app.get("/api/voices")
def list_voices():
    """List available voices (user uploads only)."""
    return {"voices": _load_voices()}


@app.post("/api/voices/upload")
async def upload_voice(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    character_statement: Optional[str] = Form(None),
):
    """
    Upload a voice: name, character statement, and audio sample (MP3).
    Saves to data/custom_voices/{voice_id}/ with sample.mp3 and config.json.
    """
    ext = Path(file.filename or "").suffix.lower()
    if ext != ".mp3":
        raise HTTPException(400, "Only MP3 files are supported for voice samples.")

    content = await file.read()
    if len(content) > MAX_VOICE_SIZE:
        raise HTTPException(400, f"File too large. Max {MAX_VOICE_SIZE // (1024*1024)} MB.")

    display_name = (name or "").strip()
    if not display_name:
        display_name = Path(file.filename or "Voice").stem

    voice_id = os.urandom(8).hex()
    voice_dir = CUSTOM_VOICES_DIR / voice_id
    voice_dir.mkdir(parents=True, exist_ok=True)

    sample_path = voice_dir / "sample.mp3"
    sample_path.write_bytes(content)

    char_stmt = (character_statement or "").strip()
    config = {
        "id": voice_id,
        "name": display_name,
        "character_statement": char_stmt,
        "filename": file.filename,
    }
    import json
    (voice_dir / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")

    return VoiceInfo(
        id=voice_id,
        name=display_name,
        character_statement=char_stmt,
    )


@app.post("/api/sources/upload")
async def upload_source(file: UploadFile = File(...)):
    """Upload a document (PDF, TXT). Returns source_id."""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in (".pdf", ".txt", ".md"):
        raise HTTPException(400, "Supported: .pdf, .txt, .md")
    path = UPLOAD_DIR / f"{os.urandom(8).hex()}{ext}"
    content = await file.read()
    path.write_bytes(content)
    return {"source_id": path.stem, "filename": file.filename}


@app.post("/api/sources/text")
async def add_text_source(body: SourceText):
    """Add pasted text as a source."""
    if not body.text.strip():
        raise HTTPException(400, "Text cannot be empty")
    path = UPLOAD_DIR / f"{os.urandom(8).hex()}.txt"
    path.write_text(body.text.strip(), encoding="utf-8")
    return {"source_id": path.stem, "filename": "pasted.txt"}


def _extract_text_from_html(html: str) -> str:
    """Extract readable text from HTML using stdlib only."""
    from html.parser import HTMLParser

    class _TextExtractor(HTMLParser):
        def __init__(self):
            super().__init__()
            self.text: list[str] = []
        def handle_data(self, data: str):
            s = data.strip()
            if s:
                self.text.append(s)
        def get_text(self) -> str:
            return "\n\n".join(self.text)

    try:
        parser = _TextExtractor()
        parser.feed(html)
        return parser.get_text()
    except Exception:
        import re
        return re.sub(r"<[^>]+>", " ", html).strip()


@app.post("/api/sources/url")
async def add_url_source(body: SourceUrl):
    """Fetch URL, extract text, and add as source."""
    url = (body.url or "").strip()
    if not url:
        raise HTTPException(400, "URL cannot be empty")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    import httpx
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            r = await client.get(url)
            r.raise_for_status()
            html = r.text
    except httpx.HTTPError as e:
        raise HTTPException(502, f"Could not fetch URL: {e}")
    text = _extract_text_from_html(html)
    if not text or len(text) < 50:
        raise HTTPException(400, "Could not extract enough text from URL. Try a different page.")
    path = UPLOAD_DIR / f"{os.urandom(8).hex()}.txt"
    path.write_text(text[:150000], encoding="utf-8")  # cap at ~150k chars
    from urllib.parse import urlparse
    name = urlparse(url).netloc or "webpage"
    return {"source_id": path.stem, "filename": f"{name}.txt"}


def _load_source_text(source_id: str) -> str:
    """Load and return text for a source. Raises FileNotFoundError if missing."""
    for ext in (".pdf", ".txt", ".md"):
        path = UPLOAD_DIR / f"{source_id}{ext}"
        if path.exists():
            if ext == ".pdf":
                from pypdf import PdfReader
                reader = PdfReader(str(path))
                return "\n\n".join(p.extract_text() or "" for p in reader.pages)
            return path.read_text(encoding="utf-8")
    raise FileNotFoundError(f"Source not found: {source_id}")


GENERATED_DIR = UPLOAD_DIR / "generated"
GENERATED_DIR.mkdir(exist_ok=True)


@app.post("/api/generate")
async def generate_overview(req: GenerateRequest):
    """Generate podcast script with LuxTTS voice and return audio."""
    from llm_service import generate_script, parse_script
    from luxtts_service import generate_speech, is_available

    if not is_available():
        from luxtts_service import get_tts_status
        st = get_tts_status()
        msg = st.get("error") or "LuxTTS not available. Check /api/tts-status for details."
        raise HTTPException(503, msg)

    from llm_service import get_llm_status
    provider = (req.provider or "local").lower()
    cloud_provider = (req.cloud_provider or "gemini").lower() if provider == "cloud" else None
    llm_st = get_llm_status(provider=provider, cloud_provider=cloud_provider, format_type=req.format)
    if not llm_st.get("available"):
        raise HTTPException(503, llm_st.get("error") or "LLM not available.")

    # Load all source text
    combined = []
    for sid in req.source_ids:
        try:
            combined.append(_load_source_text(sid))
        except FileNotFoundError:
            raise HTTPException(404, f"Source not found: {sid}")
    source_text = "\n\n---\n\n".join(combined)
    if not source_text.strip():
        raise HTTPException(400, "No text content in sources.")

    # Load character statements for selected voices
    voices_by_id = {v.id: v for v in _load_voices()}
    host1_char = voices_by_id.get(req.host1_voice_id, None)
    host2_char = voices_by_id.get(req.host2_voice_id or req.host1_voice_id, None)
    host3_char = voices_by_id.get(req.host3_voice_id or req.host1_voice_id, None)
    host1_stmt = host1_char.character_statement if host1_char else None
    host2_stmt = host2_char.character_statement if host2_char else None
    host3_stmt = host3_char.character_statement if host3_char else None

    # Generate script
    models = {
        "ollama": req.ollama_model,
        "gemini": req.gemini_model,
        "grok": req.grok_model,
        "openai": req.openai_model,
    }
    try:
        raw_script = await generate_script(
            source_text,
            req.format,
            provider=provider,
            cloud_provider=cloud_provider,
            custom_prompt=req.custom_prompt,
            host1_character=host1_stmt or None,
            host2_character=host2_stmt or None,
            host3_character=host3_stmt or None,
            models=models,
        )
    except Exception as e:
        raise HTTPException(502, f"LLM failed: {e}")

    segments = parse_script(raw_script, req.format)
    if not segments:
        raise HTTPException(500, "Could not parse script. Ensure LLM returned valid dialogue.")

    host2_voice = req.host2_voice_id or req.host1_voice_id
    host3_voice = req.host3_voice_id or req.host1_voice_id
    voice_map = {"host1": req.host1_voice_id, "host2": host2_voice, "host3": host3_voice}

    # Generate TTS for each segment
    wav_paths = []
    for speaker, text in segments:
        if not text:
            continue
        voice_id = voice_map.get(speaker, req.host1_voice_id)
        wav = await generate_speech(text, voice_id)
        if wav:
            wav_paths.append(wav)

    if not wav_paths:
        raise HTTPException(
            500,
            "TTS failed to generate audio. If using custom voices, the MP3 may be corrupt — try re-uploading."
        )

    # Stitch WAVs
    try:
        from pydub import AudioSegment
        combined_audio = AudioSegment.empty()
        for p in wav_paths:
            combined_audio += AudioSegment.from_wav(str(p))
            combined_audio += AudioSegment.silent(duration=400)  # 0.4s pause between turns
        audio_id = os.urandom(8).hex()
        out_path = GENERATED_DIR / f"{audio_id}.wav"
        combined_audio.export(str(out_path), format="wav")
    finally:
        for p in wav_paths:
            try:
                p.unlink(missing_ok=True)
            except Exception:
                pass

    return {
        "status": "ok",
        "script": raw_script,
        "audio_url": f"/api/audio/{audio_id}",
    }


@app.get("/api/audio/{audio_id}")
async def get_generated_audio(audio_id: str):
    """Serve generated WAV file."""
    path = GENERATED_DIR / f"{audio_id}.wav"
    if not path.exists():
        raise HTTPException(404, "Audio not found")
    return FileResponse(path, media_type="audio/wav", filename="overview.wav")


@app.get("/api/sources/{source_id}/text")
async def get_source_text(source_id: str):
    """Extract text from an uploaded source."""
    for ext in (".pdf", ".txt", ".md"):
        path = UPLOAD_DIR / f"{source_id}{ext}"
        if path.exists():
            if ext == ".pdf":
                try:
                    from pypdf import PdfReader
                    reader = PdfReader(str(path))
                    text = "\n".join(p.extract_text() or "" for p in reader.pages)
                    return {"source_id": source_id, "text": text}
                except Exception as e:
                    raise HTTPException(500, str(e))
            return {"source_id": source_id, "text": path.read_text(encoding="utf-8")}
    raise HTTPException(404, "Source not found")
