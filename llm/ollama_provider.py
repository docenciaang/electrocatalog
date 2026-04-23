import json
import os

import requests

from .provider_base import LLMProvider


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1].lstrip("json").strip()
    return json.loads(text)


class OllamaProvider(LLMProvider):
    def __init__(self):
        self.base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model    = os.environ.get("OLLAMA_MODEL", "llama3.2")

    def generate_structured(self, prompt: str, max_tokens: int = 1024) -> dict:
        resp = requests.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False},
            timeout=60,
        )
        resp.raise_for_status()
        return _extract_json(resp.json()["response"])
