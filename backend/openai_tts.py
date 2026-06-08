"""OpenAI TTS provider."""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from typing import Optional


async def generate(
    text: str,
    voice: str,
    model: str = "tts-1-hd",
    speed: float = 1.0,
    api_key: str = "",
) -> Optional[Path]:
    if not api_key:
        print("[OpenAI TTS] No API key configured.")
        return None

    text = text.strip()[:4096]
    if not text:
        return None

    import httpx

    loop = asyncio.get_event_loop()

    def _call():
        with httpx.Client(timeout=60.0) as client:
            r = client.post(
                "https://api.openai.com/v1/audio/speech",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "voice": voice,
                    "input": text,
                    "speed": round(max(0.25, min(4.0, speed)), 2),
                },
            )
            r.raise_for_status()
            return r.content

    try:
        audio_bytes = await loop.run_in_executor(None, _call)
    except Exception as e:
        print(f"[OpenAI TTS] Request failed: {e}")
        return None

    # OpenAI returns MP3; convert to WAV for pydub stitching
    try:
        from pydub import AudioSegment
        import io

        seg = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        tmp.close()
        seg.export(tmp.name, format="wav")
        return Path(tmp.name)
    except Exception as e:
        print(f"[OpenAI TTS] Audio conversion failed: {e}")
        return None
