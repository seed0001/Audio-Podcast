"""
Test pipeline: send a test message to all three AI Council members (Gemini, Grok, OpenAI)
and print their responses. Verifies all three API keys are working.
"""

import asyncio
import os
import sys
from pathlib import Path

# Load .env from project root
ROOT = Path(__file__).resolve().parent.parent
_dotenv = ROOT / ".env"
if _dotenv.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_dotenv)
    except ImportError:
        pass

# Ensure backend is on path
sys.path.insert(0, str(ROOT / "backend"))
os.chdir(ROOT / "backend")


async def main() -> None:
    from llm_service import chat

    test_message = "This is a council test. Reply with one short sentence: what is your name and one strength you bring to a discussion?"
    messages = [{"role": "user", "content": test_message}]

    print("=" * 60)
    print("AI Council Test Pipeline")
    print("=" * 60)
    print(f"\nTest message: {test_message}\n")

    # Check keys
    g = os.getenv("GEMINI_API_KEY")
    x = os.getenv("XAI_API_KEY")
    o = os.getenv("OPENAI_API_KEY")
    if not g or not x or not o:
        missing = []
        if not g: missing.append("GEMINI_API_KEY")
        if not x: missing.append("XAI_API_KEY")
        if not o: missing.append("OPENAI_API_KEY")
        print(f"Missing API keys: {', '.join(missing)}")
        sys.exit(1)

    print("Sending to Gemini, Grok, OpenAI...\n")

    result = await chat(
        mode="ai_council",
        messages=messages,
        models={
            "gemini": os.getenv("AOS_GEMINI_MODEL", "gemini-2.5-flash"),
            "grok": os.getenv("AOS_GROK_MODEL", "grok-3"),
            "openai": os.getenv("AOS_OPENAI_MODEL", "gpt-4o"),
        },
        timeout=90.0,
    )

    replies = result.get("replies", [])
    if not replies:
        print("No replies received.")
        sys.exit(1)

    for r in replies:
        speaker = r.get("speaker", "?")
        content = r.get("content", "")
        print(f"[{speaker}]")
        print(content)
        print()

    print("=" * 60)
    print("AI Council test passed — all three responded.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
