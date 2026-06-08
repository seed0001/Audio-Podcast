"""
LLM service — Script generation via Ollama, Gemini, Grok, or OpenAI.

Provider toggle: Local (Ollama) or Cloud (Gemini | Grok | OpenAI).
AI Council Review: all three cloud providers come together to review and debate.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any, Optional

import httpx

OLLAMA_HOST = os.getenv("AOS_OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("AOS_OLLAMA_MODEL", "llama3.2")

# Known local LLM servers to probe during auto-detection
_LOCAL_SERVERS = [
    {"name": "Ollama",              "host": "http://localhost:11434", "type": "ollama"},
    {"name": "LM Studio",           "host": "http://localhost:1234",  "type": "openai_compat"},
    {"name": "Jan",                 "host": "http://localhost:1337",  "type": "openai_compat"},
    {"name": "llama.cpp",           "host": "http://localhost:8080",  "type": "openai_compat"},
    {"name": "LocalAI",             "host": "http://localhost:8081",  "type": "openai_compat"},
    {"name": "GPT4All",             "host": "http://localhost:4891",  "type": "openai_compat"},
    {"name": "Text Gen WebUI",      "host": "http://localhost:5000",  "type": "openai_compat"},
    {"name": "Kobold.cpp",          "host": "http://localhost:5001",  "type": "openai_compat"},
    {"name": "Open WebUI",          "host": "http://localhost:3000",  "type": "openai_compat"},
]


def detect_local_llms() -> list[dict]:
    """Probe common local LLM server ports. Returns list of running servers with their models."""
    import httpx
    found = []
    for s in _LOCAL_SERVERS:
        try:
            with httpx.Client(timeout=1.5) as client:
                if s["type"] == "ollama":
                    r = client.get(f"{s['host']}/api/tags")
                    if r.status_code == 200:
                        data = r.json()
                        models = sorted({
                            m.get("name") or m.get("model", "")
                            for m in (data.get("models") or [])
                            if m.get("name") or m.get("model")
                        })
                        found.append({**s, "models": models})
                else:
                    r = client.get(f"{s['host']}/v1/models")
                    if r.status_code == 200:
                        data = r.json()
                        models = sorted({
                            m.get("id", "")
                            for m in (data.get("data") or [])
                            if m.get("id")
                        })
                        found.append({**s, "models": models})
        except Exception:
            pass
    return found


def probe_custom_host(host: str) -> dict:
    """Probe a user-supplied host URL and return its type and models."""
    import httpx
    host = host.rstrip("/")
    try:
        with httpx.Client(timeout=3.0) as client:
            # Try Ollama first
            try:
                r = client.get(f"{host}/api/tags")
                if r.status_code == 200:
                    data = r.json()
                    models = sorted({
                        m.get("name") or m.get("model", "")
                        for m in (data.get("models") or [])
                        if m.get("name") or m.get("model")
                    })
                    return {"host": host, "type": "ollama", "name": "Custom (Ollama)", "models": models, "available": True}
            except Exception:
                pass
            # Try OpenAI-compatible
            r = client.get(f"{host}/v1/models")
            if r.status_code == 200:
                data = r.json()
                models = sorted({m.get("id", "") for m in (data.get("data") or []) if m.get("id")})
                return {"host": host, "type": "openai_compat", "name": "Custom (OpenAI-compatible)", "models": models, "available": True}
    except Exception as e:
        return {"host": host, "type": "unknown", "name": "Custom", "models": [], "available": False, "error": str(e)}
    return {"host": host, "type": "unknown", "name": "Custom", "models": [], "available": False, "error": "No LLM API detected at this address"}
GEMINI_MODEL = os.getenv("AOS_GEMINI_MODEL", "gemini-2.5-flash")
OPENAI_MODEL = os.getenv("AOS_OPENAI_MODEL", "gpt-4o")
GROK_MODEL = os.getenv("AOS_GROK_MODEL", "grok-3")


def _get_model(provider: str, cloud_provider: Optional[str], models: Optional[dict]) -> Optional[str]:
    """Get model override from models dict."""
    if not models:
        return None
    if provider == "local":
        return models.get("ollama")
    return models.get(cloud_provider or "gemini")


def _call_provider(
    provider: str,
    cloud_provider: Optional[str],
    system: str,
    user: str,
    timeout: float = 120.0,
    models: Optional[dict] = None,
    local_llm_host: Optional[str] = None,
    local_llm_type: Optional[str] = None,
):
    """Route to correct provider with optional model override."""
    model = _get_model(provider, cloud_provider, models)
    if provider == "local":
        llm_type = local_llm_type or "ollama"
        llm_host = local_llm_host or OLLAMA_HOST
        if llm_type == "openai_compat":
            return _generate_openai_compat(system, user, timeout, base_url=llm_host, model=model or "default")
        return _generate_ollama(system, user, timeout, model=model, host=llm_host)
    if cloud_provider == "gemini":
        return _generate_gemini(system, user, timeout, model=model)
    if cloud_provider == "grok":
        return _generate_grok(system, user, timeout, model=model)
    if cloud_provider == "openai":
        return _generate_openai(system, user, timeout, model=model)
    return _generate_gemini(system, user, timeout, model=model)


async def generate_script(
    source_text: str,
    format_type: str,
    provider: str = "local",
    cloud_provider: Optional[str] = None,
    custom_prompt: Optional[str] = None,
    host1_character: Optional[str] = None,
    host2_character: Optional[str] = None,
    host3_character: Optional[str] = None,
    timeout: float = 120.0,
    models: Optional[dict] = None,
    local_llm_host: Optional[str] = None,
    local_llm_type: Optional[str] = None,
) -> str:
    """
    Generate podcast script. Returns raw text with Host A/B/C lines.
    For ai_council_review: all three cloud providers participate in multi-turn debate.
    """
    if format_type == "ai_council_review":
        return await _generate_council_review(source_text, custom_prompt, timeout, models=models)

    from prompt_store import load_prompts
    p = load_prompts()

    format_instructions = {
        "deep_dive": p["format_deep_dive"],
        "brief": p["format_brief"],
        "critique": p["format_critique"],
        "debate": p["format_debate"],
    }
    instructions = format_instructions.get(format_type, p["format_deep_dive"])
    focus = f"\nAdditional focus: {custom_prompt}" if custom_prompt else ""

    characters = ""
    if host1_character or host2_character:
        parts = []
        if host1_character:
            parts.append(f"Host A: {host1_character.strip()}")
        if host2_character:
            parts.append(f"Host B: {host2_character.strip()}")
        if parts:
            characters = "\nCharacter statements:\n" + "\n".join(parts) + "\n"

    system = f"""{p['scriptwriter_role']}

Format: {instructions}
{characters}{focus}

{p['script_output_instructions']}"""

    user = f"""Source material:

{source_text[:15000]}

Write the podcast script:"""

    return await _call_provider(
        provider, cloud_provider, system, user, timeout,
        models=models,
        local_llm_host=local_llm_host,
        local_llm_type=local_llm_type,
    )


async def _generate_council_review(
    source_text: str, custom_prompt: Optional[str], timeout: float, models: Optional[dict] = None
) -> str:
    """
    AI Council Review: Gemini, Grok, and OpenAI analyze, debate, and conclude.
    Multi-turn: each provider contributes in sequence.
    """
    gemini_key = os.getenv("GEMINI_API_KEY")
    xai_key = os.getenv("XAI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    if not gemini_key or not xai_key or not openai_key:
        raise RuntimeError(
            "AI Council Review requires all three: GEMINI_API_KEY, XAI_API_KEY, OPENAI_API_KEY"
        )

    from prompt_store import load_prompts
    p = load_prompts()

    focus = f"\nFocus: {custom_prompt}" if custom_prompt else ""
    intro = f"""{p['council_intro']}
{focus}

Source material:
{source_text[:12000]}"""

    lines: list[tuple[str, str]] = []
    context = ""

    gemini_m = (models or {}).get("gemini") or GEMINI_MODEL
    grok_m = (models or {}).get("grok") or GROK_MODEL
    openai_m = (models or {}).get("openai") or OPENAI_MODEL

    async def _gemini(s, u): return await _generate_gemini(s, u, timeout, model=gemini_m)
    async def _grok(s, u): return await _generate_grok(s, u, timeout, model=grok_m)
    async def _openai(s, u): return await _generate_openai(s, u, timeout, model=openai_m)

    # Round 1: Initial analysis
    for name, provider_fn, prompt_key in [
        ("Host A", _gemini, "council_r1_gemini"),
        ("Host B", _grok,   "council_r1_grok"),
        ("Host C", _openai, "council_r1_openai"),
    ]:
        system = f"{intro}\n\n{context}\n\n{p[prompt_key]}"
        try:
            out = await provider_fn(system, "Continue.")
            out = out.strip()
            if out:
                lines.append(("host1" if "Host A" in name else "host2" if "Host B" in name else "host3", out.split(":", 1)[-1].strip() if ":" in out else out))
                context += f"\n{name}: {out}\n"
        except Exception as e:
            lines.append(("host1" if "Host A" in name else "host2" if "Host B" in name else "host3", f"[Error: {e}]"))

    # Round 2: Debate
    for name, provider_fn, prompt_key in [
        ("Host A", _gemini, "council_r2_gemini"),
        ("Host B", _grok,   "council_r2_grok"),
        ("Host C", _openai, "council_r2_openai"),
    ]:
        system = f"{intro}\n\nDiscussion so far:\n{context}\n\n{p[prompt_key]}"
        try:
            out = await provider_fn(system, "Continue.")
            out = out.strip()
            if out:
                prefix = "host1" if "Host A" in name else "host2" if "Host B" in name else "host3"
                text = out.split(":", 1)[-1].strip() if ":" in out else out
                lines.append((prefix, text))
                context += f"\n{name}: {out}\n"
        except Exception:
            pass

    # Build script string for parse_script
    host_map = {"host1": "Host A", "host2": "Host B", "host3": "Host C"}
    return "\n".join(f"{host_map.get(s, 'Host A')}: {t}" for s, t in lines)


async def _generate_ollama(
    system: str, user: str, timeout: float,
    model: Optional[str] = None,
    host: Optional[str] = None,
) -> str:
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    base = (host or OLLAMA_HOST).rstrip("/")
    url = f"{base}/api/chat"
    payload = {"model": model or OLLAMA_MODEL, "messages": messages, "stream": False}
    async with httpx.AsyncClient(timeout=None) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
    return ((data.get("message") or {}).get("content") or "").strip()


async def _generate_openai_compat(
    system: str, user: str, timeout: float,
    base_url: str, model: str,
) -> str:
    """OpenAI-compatible /v1/chat/completions — works with LM Studio, Jan, llama.cpp, etc."""
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    url = f"{base_url.rstrip('/')}/v1/chat/completions"
    payload = {"model": model, "messages": messages, "stream": False}
    # Most local servers don't require auth, but some accept a dummy key
    headers = {"Authorization": "Bearer local", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=None) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
    content = (((data.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()
    if not content:
        raise RuntimeError("Empty response from local LLM")
    return content


async def _generate_gemini(system: str, user: str, timeout: float, model: Optional[str] = None) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise RuntimeError("pip install google-genai")

    def _sync():
        client = genai.Client(api_key=api_key)
        contents = f"{system}\n\n{user}"
        r = client.models.generate_content(
            model=model or GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(temperature=0.8, max_output_tokens=4096),
        )
        if not r or not r.text:
            raise RuntimeError("Gemini empty response")
        return r.text.strip()

    return await asyncio.to_thread(_sync)


async def _generate_grok(system: str, user: str, timeout: float, model: Optional[str] = None) -> str:
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        raise RuntimeError("XAI_API_KEY not set (xAI/Grok)")
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model or GROK_MODEL, "messages": messages, "stream": False}
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post("https://api.x.ai/v1/chat/completions", json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
    content = (((data.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()
    if not content:
        raise RuntimeError("Grok empty response")
    return content


async def _generate_openai(system: str, user: str, timeout: float, model: Optional[str] = None) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model or OPENAI_MODEL, "messages": messages, "stream": False}
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
    content = (((data.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()
    if not content:
        raise RuntimeError("OpenAI empty response")
    return content


def get_llm_status(
    provider: str = "local",
    cloud_provider: Optional[str] = None,
    format_type: Optional[str] = None,
    **kwargs: Any,
) -> dict:
    """Check availability for the selected provider (or all three for council)."""
    status: dict = {"provider": provider, "cloud_provider": cloud_provider, "available": False, "error": None}

    if format_type == "ai_council_review":
        g = bool(os.getenv("GEMINI_API_KEY"))
        x = bool(os.getenv("XAI_API_KEY"))
        o = bool(os.getenv("OPENAI_API_KEY"))
        status["available"] = g and x and o
        if not status["available"]:
            missing = []
            if not g: missing.append("GEMINI_API_KEY")
            if not x: missing.append("XAI_API_KEY")
            if not o: missing.append("OPENAI_API_KEY")
            status["error"] = f"AI Council Review needs all three: {', '.join(missing)}"
        return status

    if provider == "local":
        local_host = kwargs.get("local_llm_host") or OLLAMA_HOST
        local_type = kwargs.get("local_llm_type") or "ollama"
        status["local_host"] = local_host
        try:
            with httpx.Client(timeout=3.0) as client:
                if local_type == "ollama":
                    r = client.get(f"{local_host.rstrip('/')}/api/tags")
                else:
                    r = client.get(f"{local_host.rstrip('/')}/v1/models")
            status["available"] = r.status_code == 200
            if not status["available"]:
                status["error"] = f"LLM server at {local_host} returned {r.status_code}"
        except Exception:
            status["error"] = (
                f"Cannot reach local LLM at {local_host}. "
                "Make sure your LLM server is running."
            )
        return status

    # Cloud
    if cloud_provider == "gemini":
        status["available"] = bool(os.getenv("GEMINI_API_KEY"))
        status["error"] = None if status["available"] else "GEMINI_API_KEY not set"
    elif cloud_provider == "grok":
        status["available"] = bool(os.getenv("XAI_API_KEY"))
        status["error"] = None if status["available"] else "XAI_API_KEY not set (xAI/Grok)"
    elif cloud_provider == "openai":
        status["available"] = bool(os.getenv("OPENAI_API_KEY"))
        status["error"] = None if status["available"] else "OPENAI_API_KEY not set"
    else:
        status["available"] = bool(os.getenv("GEMINI_API_KEY"))
        status["error"] = None if status["available"] else "GEMINI_API_KEY not set"
    return status


async def chat(
    mode: str,
    messages: list[dict],
    provider: str = "local",
    cloud_provider: Optional[str] = None,
    chat_providers: Optional[list[str]] = None,
    character_providers: Optional[list[str]] = None,
    agent_statements: Optional[list[str]] = None,
    models: Optional[dict] = None,
    timeout: float = 60.0,
) -> dict:
    """
    Chat with one or more models. Returns { content, speaker } for single,
    or { replies: [{ speaker, content }] } for dual/triple/ai_council.
    """
    if not messages:
        return {"content": "", "speaker": None}

    from prompt_store import load_prompts
    _p = load_prompts()

    conv = "\n".join(
        f"{'User' if m.get('role') == 'user' else 'Assistant'}: {m.get('content', '')}"
        for m in messages
    )
    last_user = next((m.get("content", "") for m in reversed(messages) if m.get("role") == "user"), "")
    base_system = f"Conversation so far:\n\n{conv}\n\n{_p['chat_base_system']}"
    agent_stmts = agent_statements or []

    def _add_agent(s: str, stmt: Optional[str]) -> str:
        if stmt and stmt.strip():
            return f"{s}\n\nCharacter/profile: {stmt.strip()}"
        return s

    m = models or {}
    if mode == "single":
        sys = _add_agent(base_system, agent_stmts[0] if agent_stmts else None)
        if provider == "local":
            ollama_model = m.get("ollama") or OLLAMA_MODEL
            out = await _generate_ollama(sys, last_user, timeout, model=ollama_model)
            return {"content": out, "speaker": "Ollama"}
        p = cloud_provider or "gemini"
        speakers = {"gemini": "Gemini", "grok": "Grok", "openai": "OpenAI"}
        model_override = m.get(p) or (GEMINI_MODEL if p == "gemini" else GROK_MODEL if p == "grok" else OPENAI_MODEL)
        fns = {"gemini": _generate_gemini, "grok": _generate_grok, "openai": _generate_openai}
        fn = fns.get(p, _generate_gemini)
        out = await fn(sys, last_user, timeout, model=model_override)
        return {"content": out, "speaker": speakers.get(p, p)}

    # dual / triple: use character_providers to build providers_to_call
    char_providers = character_providers or []
    providers_to_call: list[tuple[str, Any, str, Optional[str]]] = []  # (speaker, fn, model, agent_stmt)

    def _speaker(p: str) -> str:
        return {"local": "Ollama", "gemini": "Gemini", "grok": "Grok", "openai": "OpenAI"}.get(p, p)

    if mode == "dual":
        ps = char_providers[:2] if len(char_providers) >= 2 else ["gemini", "grok"]
        stmts = (agent_stmts + [None] * 2)[:2]
        for i, p in enumerate(ps):
            stmt = stmts[i] if i < len(stmts) else None
            sys = _add_agent(base_system, stmt)
            if p == "local":
                providers_to_call.append((_speaker(p), _generate_ollama, m.get("ollama") or OLLAMA_MODEL, sys))
            else:
                mod = m.get(p) or (GEMINI_MODEL if p == "gemini" else GROK_MODEL if p == "grok" else OPENAI_MODEL)
                fn = {"gemini": _generate_gemini, "grok": _generate_grok, "openai": _generate_openai}.get(p, _generate_gemini)
                providers_to_call.append((_speaker(p), fn, mod, sys))
    elif mode == "triple":
        ps = char_providers[:3] if len(char_providers) >= 3 else ["gemini", "grok", "openai"]
        stmts = (agent_stmts + [None] * 3)[:3]
        for i, p in enumerate(ps):
            stmt = stmts[i] if i < len(stmts) else None
            sys = _add_agent(base_system, stmt)
            if p == "local":
                providers_to_call.append((_speaker(p), _generate_ollama, m.get("ollama") or OLLAMA_MODEL, sys))
            else:
                mod = m.get(p) or (GEMINI_MODEL if p == "gemini" else GROK_MODEL if p == "grok" else OPENAI_MODEL)
                fn = {"gemini": _generate_gemini, "grok": _generate_grok, "openai": _generate_openai}.get(p, _generate_gemini)
                providers_to_call.append((_speaker(p), fn, mod, sys))
    elif mode == "ai_council":
        gemini_m = m.get("gemini") or GEMINI_MODEL
        grok_m = m.get("grok") or GROK_MODEL
        openai_m = m.get("openai") or OPENAI_MODEL
        providers_to_call = [
            ("Gemini", _generate_gemini, gemini_m, base_system + "\n\n" + _p["council_chat_gemini"]),
            ("Grok",   _generate_grok,   grok_m,   base_system + "\n\n" + _p["council_chat_grok"]),
            ("OpenAI", _generate_openai, openai_m, base_system + "\n\n" + _p["council_chat_openai"]),
        ]

    if not providers_to_call:
        return {"replies": []}

    council_style = mode == "ai_council"
    replies: list[dict] = []

    for i, item in enumerate(providers_to_call):
        speaker = item[0]
        fn = item[1]
        mod = item[2] if len(item) > 2 else None
        custom_sys = item[3] if len(item) > 3 else base_system
        prior = "\n".join(f"{r['speaker']}: {r['content']}" for r in replies) if replies else ""
        sys = custom_sys
        if council_style and prior:
            sys = custom_sys + f"\n\nCouncil discussion so far:\n{prior}\n\nYou are {speaker}. Add your perspective."
        elif council_style and i > 0:
            sys = custom_sys + f"\n\nYou are {speaker}. Add your perspective."
        try:
            out = await fn(sys, last_user, timeout, model=mod)
            replies.append({"speaker": speaker, "content": out.strip()})
        except Exception as e:
            replies.append({"speaker": speaker, "content": f"[Error: {e}]"})

    return {"replies": replies}


def parse_script(raw: str, format_type: str = "deep_dive") -> list[tuple[str, str]]:
    """Parse script into [(speaker, text), ...]. Host A->host1, B->host2, C->host3."""
    segments: list[tuple[str, str]] = []
    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        lower = line.lower()
        if lower.startswith("host a:"):
            segments.append(("host1", line[7:].strip()))
        elif lower.startswith("host b:"):
            segments.append(("host2", line[7:].strip()))
        elif lower.startswith("host c:"):
            segments.append(("host3", line[7:].strip()))
    return segments
