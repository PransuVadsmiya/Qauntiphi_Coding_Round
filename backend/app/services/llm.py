"""Minimal provider-agnostic LLM client (Gemini, Groq, OpenAI) over plain HTTP.

If no provider/key is configured, `chat()` returns None and callers fall back
to their rule-based answers, so the app always works.
"""
from typing import Optional

import httpx

from ..config import settings

DEFAULT_MODELS = {
    "gemini": "gemini-2.5-flash",
    "groq": "llama-3.3-70b-versatile",
    "openai": "gpt-4o-mini",
}

OPENAI_COMPATIBLE = {
    "groq": "https://api.groq.com/openai/v1/chat/completions",
    "openai": "https://api.openai.com/v1/chat/completions",
}


class LLMError(Exception):
    pass


def chat(system: str, messages: list[dict], temperature: float = 0.4, max_tokens: int = 800) -> Optional[str]:
    """messages: [{"role": "user"|"assistant", "content": str}, ...]"""
    if not settings.llm_enabled:
        return None
    provider = settings.llm_provider
    model = settings.llm_model or DEFAULT_MODELS.get(provider, "")

    try:
        if provider == "gemini":
            return _gemini(model, system, messages, temperature, max_tokens)
        if provider in OPENAI_COMPATIBLE:
            return _openai_compatible(provider, model, system, messages, temperature, max_tokens)
    except (httpx.HTTPError, KeyError, IndexError) as e:
        raise LLMError(f"{provider} request failed: {e}") from e
    raise LLMError(f"Unknown LLM_PROVIDER '{provider}'")


def _gemini(model, system, messages, temperature, max_tokens) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [
            {"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]}
            for m in messages
        ],
        "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
    }
    r = httpx.post(url, params={"key": settings.llm_api_key}, json=body, timeout=60)
    r.raise_for_status()
    parts = r.json()["candidates"][0]["content"]["parts"]
    return "".join(p.get("text", "") for p in parts).strip()


def _openai_compatible(provider, model, system, messages, temperature, max_tokens) -> str:
    r = httpx.post(
        OPENAI_COMPATIBLE[provider],
        headers={"Authorization": f"Bearer {settings.llm_api_key}"},
        json={
            "model": model,
            "messages": [{"role": "system", "content": system}, *messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()
