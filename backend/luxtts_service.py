"""
LuxTTS voice generation service.

Uses LuxTTS from Adam GURU's temp_luxtts for text-to-speech.
All voices come from user uploads (data/custom_voices); MP3 converted to WAV for LuxTTS.
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Optional

# Paths — override with AOS_LUXTTS_PATH env var if needed
_BACKEND = Path(__file__).resolve().parent
_WORKSPACE = _BACKEND.parent
_DEFAULT_LUXTTS = _WORKSPACE.parent / "New folder (33)" / "Adam GURU" / "temp_luxtts"
_LUXTTS_PATH = Path(os.getenv("AOS_LUXTTS_PATH", str(_DEFAULT_LUXTTS)))
_CUSTOM_VOICES_DIR = _WORKSPACE / "data" / "custom_voices"

_model = None
_load_error: Optional[str] = None


def _ensure_luxtts_path() -> bool:
    import sys
    if _LUXTTS_PATH.exists() and str(_LUXTTS_PATH) not in sys.path:
        sys.path.insert(0, str(_LUXTTS_PATH))
    return _LUXTTS_PATH.exists()


def get_tts_status() -> dict:
    """Return diagnostic info for TTS setup."""
    global _load_error
    status = {
        "available": False,
        "luxtts_path": str(_LUXTTS_PATH),
        "luxtts_path_exists": _LUXTTS_PATH.exists(),
        "torch_installed": False,
        "error": None,
    }
    try:
        import torch
        status["torch_installed"] = True
        status["torch_version"] = getattr(torch, "__version__", "?")
        status["cuda_available"] = torch.cuda.is_available()
    except ImportError as e:
        status["error"] = f"torch not installed: {e}. Run: pip install torch torchaudio"
        return status

    if not _LUXTTS_PATH.exists():
        status["error"] = f"LuxTTS path not found: {_LUXTTS_PATH}. Set AOS_LUXTTS_PATH to your temp_luxtts directory."
        return status

    if is_available():
        status["available"] = True
        status["error"] = None
    else:
        status["error"] = _load_error or "LuxTTS failed to load. Check that temp_luxtts has zipvoice and all deps (lhotse, vocos, transformers, etc)."

    return status


def _resolve_voice_path(voice_id: str) -> Optional[Path]:
    """Resolve voice_id to a WAV file path. Converts MP3 to WAV for LuxTTS."""
    custom_mp3 = _CUSTOM_VOICES_DIR / voice_id / "sample.mp3"
    if not custom_mp3.exists():
        return None
    # LuxTTS expects WAV; convert MP3 to temp WAV
    try:
        from pydub import AudioSegment
        seg = AudioSegment.from_mp3(str(custom_mp3))
    except Exception as e:
        print(f"[LuxTTS] Invalid MP3 for voice {voice_id}: {e}. Re-upload a valid MP3.")
        return None
    try:
        # Use first 5–10 seconds for voice cloning (LuxTTS encode_prompt duration=5)
        ms = min(len(seg), 10000)
        seg = seg[:ms]
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        tmp.close()
        seg.export(tmp.name, format="wav")
        return Path(tmp.name)
    except Exception as e:
        print(f"[LuxTTS] MP3→WAV conversion failed for voice {voice_id}: {e}. Re-upload a valid MP3.")
        return None


def _load_model():
    global _model, _load_error
    if _model is not None:
        return _model
    if not _ensure_luxtts_path():
        _load_error = f"LuxTTS path not found: {_LUXTTS_PATH}"
        return None
    try:
        from zipvoice.luxvoice import LuxTTS
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        if device == "cpu" and hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            device = "mps"
        _model = LuxTTS("YatharthS/LuxTTS", device=device)
        _load_error = None
        return _model
    except Exception as e:
        _load_error = str(e)
        print(f"[LuxTTS] Load failed: {e}")
        return None


def is_available() -> bool:
    """Return True if LuxTTS can be loaded."""
    return _load_model() is not None


async def generate_speech(text: str, voice_id: str, speed: float = 0.9) -> Optional[Path]:
    """
    Generate TTS audio for text using the given voice.
    Returns path to temp WAV file, or None on failure.
    """
    model = _load_model()
    if not model:
        return None

    voice_path = _resolve_voice_path(voice_id)
    if not voice_path or not voice_path.exists():
        print(f"[LuxTTS] Voice not found: {voice_id}")
        return None

    text = (text or "").strip()[:2000]
    if not text:
        return None

    loop = asyncio.get_event_loop()

    def _run():
        import soundfile as sf
        import numpy as np
        encoded = model.encode_prompt(str(voice_path), rms=0.01, duration=5)
        wav = model.generate_speech(text, encoded, num_steps=6, t_shift=0.9, speed=speed, return_smooth=False)
        if hasattr(wav, "detach"):
            arr = wav.detach().cpu().numpy().squeeze()
        else:
            arr = np.array(wav).squeeze()
        arr = arr.astype(np.float64)
        peak = np.max(np.abs(arr))
        if peak > 1e-6:
            arr = arr / peak * 0.95
        arr = np.clip(arr, -1.0, 1.0).astype(np.float32)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        tmp.close()
        sf.write(tmp.name, arr, 48000)
        return Path(tmp.name)

    try:
        return await loop.run_in_executor(None, _run)
    except Exception as e:
        print(f"[LuxTTS] Generate failed: {e}")
        return None
