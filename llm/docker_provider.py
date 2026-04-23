import json
import os

from openai import OpenAI

from .provider_base import LLMProvider


class DockerModelProvider(LLMProvider):
    def __init__(self):
        self.base_url = os.environ.get("DOCKER_MODEL_BASE_URL", "http://localhost:12434/engines/llama.cpp/v1")
        self.model    = os.environ.get("DOCKER_MODEL", "ai/qwen3:latest")
        self.client   = OpenAI(base_url=self.base_url, api_key="docker")

    def generate_structured(self, prompt: str, max_tokens: int = 1024) -> dict:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "/no_think"},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens * 4,  # margen extra para modelos de razonamiento
        )
        # Qwen3 y modelos thinking ponen la respuesta en content o reasoning_content
        choice  = resp.choices[0].message
        text    = (choice.content or "").strip()
        if not text:
            # Fallback: buscar JSON dentro del reasoning_content
            reasoning = getattr(choice, "reasoning_content", "") or ""
            start = reasoning.rfind("{")
            end   = reasoning.rfind("}") + 1
            text  = reasoning[start:end] if start != -1 else ""
        # Eliminar bloque markdown si el modelo lo devuelve
        if text.startswith("```"):
            parts = text.split("```")
            text = parts[1].lstrip("json").strip()
        return json.loads(text)
