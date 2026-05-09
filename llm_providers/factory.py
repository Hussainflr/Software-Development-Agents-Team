from dataclasses import dataclass

from backend.app.config import get_settings


@dataclass(frozen=True)
class ProviderOption:
    id: str
    label: str
    default_model: str
    requires_api_key: bool


PROVIDER_OPTIONS = [
    ProviderOption("ollama", "Ollama", "qwen3:4b", False),
    ProviderOption("openai", "OpenAI", "gpt-4o-mini", True),
    ProviderOption("anthropic", "Claude/Anthropic", "claude-3-5-sonnet-latest", True),
]


def normalize_provider(provider: str | None) -> str:
    cleaned = (provider or "ollama").strip().lower()
    aliases = {
        "claude": "anthropic",
        "anthropic": "anthropic",
        "openai": "openai",
        "ollama": "ollama",
    }
    if cleaned not in aliases:
        raise ValueError(f"Unsupported provider '{provider}'. Choose Ollama, OpenAI, or Claude/Anthropic.")
    return aliases[cleaned]


def normalize_model_name(provider: str, model: str | None) -> str:
    settings = get_settings()
    selected = (model or settings.llm_model).strip()
    if provider == "ollama":
        return selected if selected.startswith("ollama/") else f"ollama/{selected}"
    if provider == "openai":
        return selected if selected.startswith("openai/") else f"openai/{selected}"
    if provider == "anthropic":
        return selected if selected.startswith("anthropic/") else f"anthropic/{selected}"
    return selected


def build_llm_client(provider: str | None = None, model: str | None = None):
    from llm_providers.litellm_client import LiteLLMClient

    settings = get_settings()
    normalized_provider = normalize_provider(provider or settings.llm_provider)
    normalized_model = normalize_model_name(normalized_provider, model or settings.llm_model)
    api_base = settings.ollama_base_url if normalized_provider == "ollama" else None
    return LiteLLMClient(provider=normalized_provider, model=normalized_model, api_base=api_base)


def provider_options() -> list[dict[str, str | bool]]:
    return [option.__dict__ for option in PROVIDER_OPTIONS]
