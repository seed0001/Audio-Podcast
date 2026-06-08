"""
Kokoro TTS provider — local, no API key needed.

Install: pip install kokoro[en]
On Windows: pip install kokoro[en] misaki[en]
On Mac/Linux: pip install kokoro[en]
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from typing import Optional

_pipeline_cache: dict = {}


def _get_pipeline(lang_code: str):
    """Load and cache the Kokoro pipeline for a given language."""
    if lang_code not in _pipeline_cache:
        from kokoro import KPipeline
        _pipeline_cache[lang_code] = KPipeline(lang_code=lang_code)
    return _pipeline_cache[lang_code]


def _voice_to_lang(voice: str) -> str:
    """Map voice name prefix to Kokoro lang_code."""
    prefix = voice[:2] if len(voice) >= 2 else "af"
    return {
        "af": "a",  # American English female
        "am": "a",  # American English male
        "bf": "b",  # British English female
        "bm": "b",  # British English male
    }.get(prefix, "a")


def _run_kokoro(text: str, voice: str, speed: float) -> Path:
    import numpy as np
    import soundfile as sf

    lang_code = _voice_to_lang(voice)
    pipeline = _get_pipeline(lang_code)

    chunks = []
    for _, _, audio in pipeline(text, voice=voice, speed=speed, split_pattern=r"[.!?]+"):
        if audio is not None and len(audio) > 0:
            chunks.append(audio)

    if not chunks:
        raise RuntimeError("Kokoro generated no audio")

    combined = np.concatenate(chunks) if len(chunks) > 1 else chunks[0]

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp.close()
    sf.write(tmp.name, combined, 24000)
    return Path(tmp.name)


async def generate(text: str, voice: str, speed: float = 1.0) -> Optional[Path]:
    text = text.strip()[:3000]
    if not text:
        return None

    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, _run_kokoro, text, voice, speed)
    except ImportError:
        print("[Kokoro TTS] Not installed. Run: pip install kokoro[en]")
        return None
    except Exception as e:
        print(f"[Kokoro TTS] Generation failed: {e}")
        return None
