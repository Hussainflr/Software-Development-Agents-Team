import os
from typing import Any

import httpx

from backend.app.config import get_settings
from llm_providers.base import ProviderConfigurationError, ProviderConnectionError


class LangChainChatProvider:
    """Provider facade that validates config and returns native LangChain chat models."""

    def __init__(self, provider: str, model: str, api_base: str | None = None) -> None:
        self.provider = provider
        self.model = model
        self.api_base = api_base
        self._chat_model = self._build_chat_model()

    @property
    def chat_model(self) -> Any:
        return self._chat_model

    def validate(self) -> None:
        self._validate_provider_ready()

    def _build_chat_model(self) -> Any:
        if self.provider == "ollama":
            from langchain_ollama import ChatOllama

            model_name = self.model.removeprefix("ollama/")
            return ChatOllama(model=model_name, base_url=self.api_base)
        if self.provider == "openai":
            from langchain_openai import ChatOpenAI

            return ChatOpenAI(model=self.model.removeprefix("openai/"))
        if self.provider == "anthropic":
            from langchain_anthropic import ChatAnthropic

            return ChatAnthropic(model=self.model.removeprefix("anthropic/"))
        raise ProviderConfigurationError(f"Unsupported provider: {self.provider}")

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
