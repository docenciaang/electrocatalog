import json
import os

import anthropic

from .provider_base import LLMProvider


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


class AnthropicProvider(LLMProvider):
    MODEL = "claude-haiku-4-5-20251001"

    def __init__(self):
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise KeyError("ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=api_key)

    def generate_structured(self, prompt: str, max_tokens: int = 1024) -> dict:
        msg = self.client.messages.create(
            model=self.MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return _extract_json(msg.content[0].text)
