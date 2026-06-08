"""ElevenLabs TTS provider."""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from typing import Optional


async def generate(
    text: str,
    voice_id: str,
    model_id: str = "eleven_turbo_v2_5",
    api_key: str = "",
) -> Optional[Path]:
    if not api_key:
        print("[ElevenLabs TTS] No API key configured.")
        return None

    text = text.strip()[:5000]
    if not text:
        return None

    import httpx

    loop = asyncio.get_event_loop()

    def _call():
        with httpx.Client(timeout=60.0) as client:
            r = client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                headers={
                    "xi-api-key": api_key,
                    "Content-Type": "application/json",
                    "Accept": "audio/mpeg",
                },
                json={
                    "text": text,
                    "model_id": model_id,
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75,
                        "style": 0.0,
                        "use_speaker_boost": True,
                    },
                },
            )
            r.raise_for_status()
            return r.content

    try:
        audio_bytes = await loop.run_in_executor(None, _call)
    except Exception as e:
        print(f"[ElevenLabs TTS] Request failed: {e}")
        return None

    try:
        from pydub import AudioSegment
        import io

        seg = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        tmp.close()
        seg.export(tmp.name, format="wav")
        return Path(tmp.name)
    except Exception as e:
        print(f"[ElevenLabs TTS] Audio conversion failed: {e}")
        return None
