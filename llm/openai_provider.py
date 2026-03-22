import json
import os

from openai import OpenAI

from .provider_base import LLMProvider


class OpenAIProvider(LLMProvider):
    MODEL = "gpt-4o-mini"

    def __init__(self):
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise KeyError("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)

    def generate_structured(self, prompt: str, max_tokens: int = 1024) -> dict:
        resp = self.client.chat.completions.create(
            model=self.MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        return json.loads(resp.choices[0].message.content)
