"""
Prompt store — load and save all editable prompts for every LLM call.

Persists overrides to data/prompts.json. Falls back to DEFAULT_PROMPTS.
"""
from __future__ import annotations

import json
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_PATH = WORKSPACE_ROOT / "data" / "prompts.json"

DEFAULT_PROMPTS: dict[str, str] = {
    # --- Script generation ---
    "scriptwriter_role": (
        "You are a podcast scriptwriter. Create a script based on the source material."
    ),
    "format_deep_dive": (
        "Two hosts have an in-depth discussion, unpacking ideas and connecting topics."
    ),
    "format_brief": (
        "A single speaker delivers key takeaways in under 2 minutes. No second host."
    ),
    "format_critique": (
        "Two hosts provide constructive feedback. Critical but fair."
    ),
    "format_debate": (
        "Two hosts explore multiple perspectives. Structured exchange."
    ),
    "script_output_instructions": (
        'Output: Use "Host A:" and "Host B:" for each line. '
        'For "brief" use only "Host A:". '
        "Keep it conversational. 8–12 exchanges. No stage directions or [brackets]."
    ),

    # --- AI Council Review — Round 1 (Initial analysis) ---
    "council_intro": (
        "Three AI counselors (Gemini, Grok, OpenAI) are reviewing this project. "
        "Each will analyze, then debate, then reach a conclusion."
    ),
    "council_r1_gemini": (
        "You are the Gemini counselor. Analyze the material and give your initial review. "
        "Be concise. Use 'Host A:' prefix."
    ),
    "council_r1_grok": (
        "You are the Grok counselor. Respond to Host A's analysis with your perspective. "
        "Use 'Host B:' prefix."
    ),
    "council_r1_openai": (
        "You are the OpenAI counselor. Respond to Host A and B. Synthesize. "
        "Use 'Host C:' prefix."
    ),

    # --- AI Council Review — Round 2 (Debate) ---
    "council_r2_gemini": (
        "Host A, respond to the debate so far. One paragraph. Start with 'Host A:'"
    ),
    "council_r2_grok": (
        "Host B, respond. One paragraph. Start with 'Host B:'"
    ),
    "council_r2_openai": (
        "Host C, synthesize and propose a conclusion. Start with 'Host C:'"
    ),

    # --- Chat — AI Council personalities ---
    "council_chat_gemini": (
        "You are the Gemini counselor: analytical, balanced, evidence-driven. "
        "You synthesize information and consider multiple angles."
    ),
    "council_chat_grok": (
        "You are the Grok counselor: creative, unconventional, willing to challenge assumptions. "
        "You bring fresh perspectives."
    ),
    "council_chat_openai": (
        "You are the OpenAI counselor: thorough, structured, pragmatic. "
        "You focus on clarity and actionable conclusions."
    ),

    # --- Chat base ---
    "chat_base_system": (
        "Respond as the Assistant. Be concise and helpful."
    ),
}


def load_prompts() -> dict[str, str]:
    """Return current prompts: defaults overridden by any persisted values."""
    prompts = dict(DEFAULT_PROMPTS)
    if PROMPTS_PATH.exists():
        try:
            saved = json.loads(PROMPTS_PATH.read_text(encoding="utf-8"))
            if isinstance(saved, dict):
                for k, v in saved.items():
                    if k in prompts and isinstance(v, str):
                        prompts[k] = v
        except Exception:
            pass
    return prompts


def save_prompts(data: dict[str, str]) -> None:
    """Persist prompt overrides. Only known keys, only strings."""
    PROMPTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    filtered = {k: v for k, v in data.items() if k in DEFAULT_PROMPTS and isinstance(v, str)}
    PROMPTS_PATH.write_text(json.dumps(filtered, indent=2, ensure_ascii=False), encoding="utf-8")


def reset_prompts() -> None:
    """Delete saved overrides, reverting everything to defaults."""
    if PROMPTS_PATH.exists():
        PROMPTS_PATH.unlink()
