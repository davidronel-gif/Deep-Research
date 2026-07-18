import os
import types
import anthropic
from typing import Any

import requests


class _TextContent:
    def __init__(self, text: str) -> None:
        self.text = text


class _MessageResponse:
    def __init__(self, text: str) -> None:
        self.content = [_TextContent(text)]


def create_chat_completion(model: str, messages: list[dict[str, Any]], max_tokens: int = 1000) -> _MessageResponse:
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key:
        base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        url = f"{base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {openrouter_key}",
            "Content-Type": "application/json",
        }
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return _MessageResponse(content)

    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        import anthropic
        client = anthropic.Anthropic(api_key=anthropic_key)
        response = client.messages.create(model=model, max_tokens=max_tokens, messages=messages)
        return response

    raise RuntimeError("Missing OPENROUTER_API_KEY or ANTHROPIC_API_KEY in environment")
