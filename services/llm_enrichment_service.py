import os

from llm.anthropic_provider import AnthropicProvider
from llm.docker_provider import DockerModelProvider
from llm.ollama_provider import OllamaProvider
from llm.openai_provider import OpenAIProvider
from llm.prompt_builder import build_prompt
from llm.provider_base import LLMProvider
from llm.schemas import get_schema

_PROVIDERS = {
    "anthropic": AnthropicProvider,
    "openai":    OpenAIProvider,
    "ollama":    OllamaProvider,
    "docker":    DockerModelProvider,
}


def get_provider(name: str | None = None) -> LLMProvider:
    name = name or os.environ.get("LLM_PROVIDER", "anthropic")
    cls  = _PROVIDERS.get(name)
    if cls is None:
        raise ValueError(f"Proveedor desconocido: {name!r}. Usa: {list(_PROVIDERS)}")
    return cls()


def _is_empty(value) -> bool:
    """Considera vacío: None, False (booleanos), cadena vacía."""
    if value is None:
        return True
    if isinstance(value, bool):
        return not value
    if isinstance(value, str):
        return value.strip() == ""
    return False


def enrich_component(component, provider_name: str | None = None) -> dict:
    """
    Llama al LLM para sugerir valores para los campos vacíos del componente.
    Devuelve un dict con los campos sugeridos (solo los que el LLM pudo deducir).
    No modifica el componente ni la base de datos.
    """
    tipo   = component.category.tipo if component.category else None
    schema = get_schema(tipo)

    # Campos del schema que están vacíos en el componente
    empty_fields = [
        f for f in schema.model_fields
        if _is_empty(getattr(component, f, None))
    ]

    if not empty_fields:
        return {}

    provider = get_provider(provider_name)
    prompt   = build_prompt(component.name, tipo, empty_fields)
    raw      = provider.generate_structured(prompt)

    # Validar con Pydantic: descarta campos inesperados y valida rangos
    validated = schema(**{k: v for k, v in raw.items() if k in schema.model_fields})

    _URL_FIELDS = {"datasheet_url", "image_url", "pinout_url"}

    # Devolver solo campos con valor (no null); URLs sin resultado → "No encontrado"
    result = {}
    for k, v in validated.model_dump().items():
        if v is not None:
            result[k] = v
        elif k in _URL_FIELDS and k in empty_fields:
            result[k] = "No encontrado"
    return result
