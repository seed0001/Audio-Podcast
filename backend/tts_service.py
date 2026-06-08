"""
TTS service — unified orchestrator for all TTS providers.

Providers: openai | elevenlabs | kokoro | luxtts
Config is loaded from data/tts_config.json (UI-settable) with env-var overrides.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Optional

_BACKEND = Path(__file__).resolve().parent
_WORKSPACE = _BACKEND.parent
_CONFIG_PATH = _WORKSPACE / "data" / "tts_config.json"

_DEFAULT_CONFIG = {
    "active_provider": "openai",
    "openai_api_key": "",
    "openai_model": "tts-1-hd",
    "elevenlabs_api_key": "",
    "elevenlabs_model": "eleven_turbo_v2_5",
    "luxtts_path": "",
}


def load_config() -> dict:
    cfg = dict(_DEFAULT_CONFIG)
    if _CONFIG_PATH.exists():
        try:
            saved = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
            cfg.update({k: v for k, v in saved.items() if k in _DEFAULT_CONFIG})
        except Exception:
            pass
    # Env vars always override saved config
    if os.getenv("OPENAI_API_KEY"):
        cfg["openai_api_key"] = os.getenv("OPENAI_API_KEY", "")
    if os.getenv("ELEVENLABS_API_KEY"):
        cfg["elevenlabs_api_key"] = os.getenv("ELEVENLABS_API_KEY", "")
    if os.getenv("AOS_LUXTTS_PATH"):
        cfg["luxtts_path"] = os.getenv("AOS_LUXTTS_PATH", "")
    if os.getenv("AOS_TTS_PROVIDER"):
        cfg["active_provider"] = os.getenv("AOS_TTS_PROVIDER", "openai")
    return cfg


def save_config(updates: dict) -> dict:
    """Save non-sensitive config fields. API keys are stored locally for convenience."""
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    current = load_config()
    allowed = set(_DEFAULT_CONFIG.keys())
    for k, v in updates.items():
        if k in allowed and v is not None:
            current[k] = v
    # Don't write empty key strings back if env var already provides them
    to_save = dict(current)
    if os.getenv("OPENAI_API_KEY") and not updates.get("openai_api_key"):
        to_save.pop("openai_api_key", None)
    if os.getenv("ELEVENLABS_API_KEY") and not updates.get("elevenlabs_api_key"):
        to_save.pop("elevenlabs_api_key", None)
    _CONFIG_PATH.write_text(json.dumps(to_save, indent=2), encoding="utf-8")
    return load_config()


# ---------------------------------------------------------------------------
# Provider status
# ---------------------------------------------------------------------------

def _openai_status(cfg: dict) -> dict:
    key = cfg.get("openai_api_key", "")
    if not key:
        return {"available": False, "reason": "OpenAI API key not configured"}
    return {"available": True, "reason": None}


def _elevenlabs_status(cfg: dict) -> dict:
    key = cfg.get("elevenlabs_api_key", "")
    if not key:
        return {"available": False, "reason": "ElevenLabs API key not configured"}
    return {"available": True, "reason": None}


def _kokoro_status() -> dict:
    try:
        import kokoro  # noqa: F401
        return {"available": True, "reason": None}
    except ImportError:
        return {
            "available": False,
            "reason": "Kokoro not installed. Run: pip install kokoro[en]",
        }


def _luxtts_status(cfg: dict) -> dict:
    path_str = cfg.get("luxtts_path", "")
    if not path_str:
        return {
            "available": False,
            "reason": "LuxTTS path not configured. Set it in TTS Setup or via AOS_LUXTTS_PATH.",
        }
    p = Path(path_str)
    if not p.exists():
        return {"available": False, "reason": f"LuxTTS path not found: {p}"}
    try:
        import torch  # noqa: F401
    except ImportError:
        return {"available": False, "reason": "torch not installed. Run: pip install torch torchaudio"}
    return {"available": True, "reason": None}


def get_all_status() -> dict:
    cfg = load_config()
    return {
        "active_provider": cfg["active_provider"],
        "openai_api_key_set": bool(cfg.get("openai_api_key")),
        "openai_model": cfg.get("openai_model", "tts-1-hd"),
        "elevenlabs_api_key_set": bool(cfg.get("elevenlabs_api_key")),
        "elevenlabs_model": cfg.get("elevenlabs_model", "eleven_turbo_v2_5"),
        "luxtts_path": cfg.get("luxtts_path", ""),
        "providers": {
            "openai": _openai_status(cfg),
            "elevenlabs": _elevenlabs_status(cfg),
            "kokoro": _kokoro_status(),
            "luxtts": _luxtts_status(cfg),
        },
    }


# ---------------------------------------------------------------------------
# Voice lists
# ---------------------------------------------------------------------------

OPENAI_VOICES = [
    {"id": "openai:alloy",   "name": "Alloy",   "description": "Neutral, balanced"},
    {"id": "openai:echo",    "name": "Echo",    "description": "Male, clear"},
    {"id": "openai:fable",   "name": "Fable",   "description": "Male, British accent"},
    {"id": "openai:onyx",    "name": "Onyx",    "description": "Male, deep"},
    {"id": "openai:nova",    "name": "Nova",    "description": "Female, warm"},
    {"id": "openai:shimmer", "name": "Shimmer", "description": "Female, soft"},
]

ELEVENLABS_VOICES = [
    {"id": "elevenlabs:21m00Tcm4TlvDq8ikWAM", "name": "Rachel",  "description": "Calm, female"},
    {"id": "elevenlabs:AZnzlk1XvdvUeBnXmlld", "name": "Domi",    "description": "Strong, female"},
    {"id": "elevenlabs:EXAVITQu4vr4xnSDxMaL", "name": "Bella",   "description": "Soft, female"},
    {"id": "elevenlabs:ErXwobaYiN019PkySvjV",  "name": "Antoni",  "description": "Well-rounded, male"},
    {"id": "elevenlabs:TxGEqnHWrfWFTfGW9XjX",  "name": "Josh",    "description": "Deep, male"},
    {"id": "elevenlabs:VR6AewLTigWG4xSOukaG",  "name": "Arnold",  "description": "Crisp, male"},
    {"id": "elevenlabs:pNInz6obpgDQGcFmaJgB",  "name": "Adam",    "description": "Deep, male narrator"},
    {"id": "elevenlabs:yoZ06aMxZJJ28mfd3POQ",  "name": "Sam",     "description": "Raspy, male"},
]

KOKORO_VOICES = [
    {"id": "kokoro:af_heart",    "name": "Heart",    "description": "US Female, warm"},
    {"id": "kokoro:af_bella",    "name": "Bella",    "description": "US Female, bright"},
    {"id": "kokoro:af_nicole",   "name": "Nicole",   "description": "US Female, natural"},
    {"id": "kokoro:af_sarah",    "name": "Sarah",    "description": "US Female, clear"},
    {"id": "kokoro:af_sky",      "name": "Sky",      "description": "US Female, airy"},
    {"id": "kokoro:am_adam",     "name": "Adam",     "description": "US Male, deep"},
    {"id": "kokoro:am_michael",  "name": "Michael",  "description": "US Male, calm"},
    {"id": "kokoro:bf_emma",     "name": "Emma",     "description": "British Female"},
    {"id": "kokoro:bf_isabella", "name": "Isabella", "description": "British Female, elegant"},
    {"id": "kokoro:bm_george",   "name": "George",   "description": "British Male"},
    {"id": "kokoro:bm_lewis",    "name": "Lewis",    "description": "British Male, warm"},
]


def get_builtin_voices(provider: Optional[str] = None) -> list[dict]:
    cfg = load_config()
    active = provider or cfg["active_provider"]
    if active == "openai":
        return OPENAI_VOICES
    if active == "elevenlabs":
        return ELEVENLABS_VOICES
    if active == "kokoro":
        return KOKORO_VOICES
    return []


def get_all_voices(custom_voices: list[dict]) -> list[dict]:
    """Return built-in voices for active provider + custom uploads (for luxtts)."""
    cfg = load_config()
    active = cfg["active_provider"]
    builtin = get_builtin_voices(active)
    voices = [
        {**v, "provider": active, "type": "builtin", "character_statement": ""}
        for v in builtin
    ]
    # Always include custom voices for luxtts; also show them when luxtts is active
    for v in custom_voices:
        voices.append({
            "id": f"luxtts:{v['id']}",
            "name": v["name"],
            "provider": "luxtts",
            "type": "custom",
            "character_statement": v.get("character_statement", ""),
        })
    return voices


# ---------------------------------------------------------------------------
# Speech generation — dispatch by voice_id prefix
# ---------------------------------------------------------------------------

async def generate_speech(text: str, voice_id: str, speed: float = 1.0) -> Optional[Path]:
    """Route TTS request to the appropriate provider based on voice_id prefix."""
    text = (text or "").strip()
    if not text:
        return None

    if ":" in voice_id:
        provider, voice_key = voice_id.split(":", 1)
    else:
        # Legacy bare ID = luxtts custom voice
        provider, voice_key = "luxtts", voice_id

    cfg = load_config()

    if provider == "openai":
        from openai_tts import generate as openai_generate
        return await openai_generate(
            text,
            voice_key,
            model=cfg.get("openai_model", "tts-1-hd"),
            speed=speed,
            api_key=cfg.get("openai_api_key", ""),
        )

    if provider == "elevenlabs":
        from elevenlabs_tts import generate as el_generate
        return await el_generate(
            text,
            voice_key,
            model_id=cfg.get("elevenlabs_model", "eleven_turbo_v2_5"),
            api_key=cfg.get("elevenlabs_api_key", ""),
        )

    if provider == "kokoro":
        from kokoro_tts import generate as kokoro_generate
        return await kokoro_generate(text, voice_key, speed=speed)

    if provider == "luxtts":
        import os
        if cfg.get("luxtts_path"):
            os.environ["AOS_LUXTTS_PATH"] = cfg["luxtts_path"]
        from luxtts_service import generate_speech as luxtts_generate
        return await luxtts_generate(text, voice_key, speed=speed)

    print(f"[TTS] Unknown provider: {provider}")
    return None


def is_active_provider_available() -> bool:
    status = get_all_status()
    provider = status["active_provider"]
    return status["providers"].get(provider, {}).get("available", False)
