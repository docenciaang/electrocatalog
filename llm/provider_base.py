from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    def generate_structured(self, prompt: str, max_tokens: int = 1024) -> dict:
        """Llama al modelo y devuelve un dict con el JSON parseado.
        Lanza ValueError si la respuesta no es JSON válido."""
        ...
