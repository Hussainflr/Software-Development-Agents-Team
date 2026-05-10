import os
from typing import Any

import httpx

from backend.app.config import get_settings
from llm_providers.base import ProviderConfigurationError, ProviderConnectionError, ProviderModelNotFoundError


def list_ollama_models(base_url: str | None = None) -> list[str]:
    """Return locally installed Ollama model names from `/api/tags`."""

    settings = get_settings()
    resolved_base_url = (base_url or settings.ollama_base_url).rstrip("/")
    try:
        response = httpx.get(f"{resolved_base_url}/api/tags", timeout=2.0)
        response.raise_for_status()
    except Exception as exc:
        raise ProviderConnectionError(
            "Ollama is not reachable at "
            f"{resolved_base_url}. Start it with `ollama serve`; Mission Control will auto-detect installed models."
        ) from exc

    models: list[str] = []
    for item in response.json().get("models", []):
        for key in ("name", "model"):
            value = item.get(key)
            if value and value not in models:
                models.append(str(value))
    return models


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
            return ChatOllama(model=model_name, base_url=self.api_base, temperature=0.2)
        if self.provider == "openai":
            from langchain_openai import ChatOpenAI

            return ChatOpenAI(model=self.model.removeprefix("openai/"), temperature=0.2)
        if self.provider == "anthropic":
            from langchain_anthropic import ChatAnthropic

            return ChatAnthropic(model=self.model.removeprefix("anthropic/"), temperature=0.2)
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
        models = list_ollama_models(base_url)
        selected_model = self.model.removeprefix("ollama/")
        if not self._model_is_installed(selected_model, models):
            available = ", ".join(models) if models else "none"
            raise ProviderModelNotFoundError(
                f"Ollama is running, but model '{selected_model}' is not installed. "
                f"Available local models: {available}. Select an installed model or use auto-detect."
            )

    @staticmethod
    def _model_is_installed(selected_model: str, installed_models: list[str]) -> bool:
        if selected_model in installed_models:
            return True
        if ":" not in selected_model and f"{selected_model}:latest" in installed_models:
            return True
        return False
