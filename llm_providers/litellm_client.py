import os

import httpx
from litellm import completion

from backend.app.config import get_settings
from llm_providers.base import ChatMessage, ProviderConfigurationError, ProviderConnectionError


class LiteLLMClient:
    """Small wrapper around LiteLLM with provider-specific validation."""

    def __init__(self, provider: str, model: str, api_base: str | None = None) -> None:
        self.provider = provider
        self.model = model
        self.api_base = api_base

    def generate(self, messages: list[ChatMessage], temperature: float = 0.2) -> str:
        self._validate_provider_ready()
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
            }
            if self.provider == "ollama" and self.api_base:
                kwargs["api_base"] = self.api_base

            response = completion(**kwargs)
            message = response["choices"][0]["message"]["content"]
            return str(message).strip()
        except ProviderConnectionError:
            raise
        except Exception as exc:  # LiteLLM raises provider-specific exception classes.
            raise ProviderConnectionError(
                f"{self.provider} failed while calling model '{self.model}': {exc}"
            ) from exc

    def _validate_provider_ready(self) -> None:
        if self.provider == "ollama":
            self._check_ollama()
        elif self.provider == "openai" and not os.getenv("OPENAI_API_KEY"):
            raise ProviderConfigurationError("OPENAI_API_KEY is required when provider is OpenAI.")
        elif self.provider == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
            raise ProviderConfigurationError("ANTHROPIC_API_KEY is required when provider is Claude/Anthropic.")

    def _check_ollama(self) -> None:
        settings = get_settings()
        base_url = self.api_base or settings.ollama_base_url
        try:
            response = httpx.get(f"{base_url.rstrip('/')}/api/tags", timeout=2.0)
            response.raise_for_status()
        except Exception as exc:
            raise ProviderConnectionError(
                "Ollama is not reachable at "
                f"{base_url}. Start it with `ollama serve` and pull a model with "
                "`ollama pull qwen2.5-coder` or `ollama pull llama3.1`."
            ) from exc

