from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelProviderCapability:
    provider: str
    label: str
    local_first: bool
    default_model: str
    supports_streaming: bool
    supports_tools: bool
    supports_vision: bool = False
    requires_api_key: bool = False


MODEL_PROVIDER_CATALOG: dict[str, ModelProviderCapability] = {
    "ollama": ModelProviderCapability("ollama", "Ollama", True, "qwen2.5-coder", True, False),
    "lmstudio": ModelProviderCapability("lmstudio", "LM Studio", True, "local-model", True, False),
    "openai": ModelProviderCapability("openai", "OpenAI", False, "gpt-4o-mini", True, True, True, True),
    "anthropic": ModelProviderCapability(
        "anthropic",
        "Claude/Anthropic",
        False,
        "claude-3-5-sonnet-latest",
        True,
        True,
        True,
        True,
    ),
    "gemini": ModelProviderCapability("gemini", "Gemini", False, "gemini-1.5-pro", True, True, True, True),
    "groq": ModelProviderCapability("groq", "Groq", False, "llama-3.1-70b-versatile", True, True, False, True),
    "openrouter": ModelProviderCapability("openrouter", "OpenRouter", False, "openrouter/auto", True, True, True, True),
    "together": ModelProviderCapability("together", "Together AI", False, "meta-llama/Llama-3.3-70B-Instruct-Turbo", True, True, False, True),
}


def list_model_provider_capabilities() -> list[ModelProviderCapability]:
    return list(MODEL_PROVIDER_CATALOG.values())
