from dataclasses import dataclass

from backend.app.config import get_settings
from config.defaults import ANTHROPIC_DEFAULT_MODEL, DEFAULT_MODEL, DEFAULT_PROVIDER, OPENAI_DEFAULT_MODEL
from llm_providers.base import ProviderConnectionError, ProviderModelNotFoundError


@dataclass(frozen=True)
class ProviderOption:
    id: str
    label: str
    default_model: str
    requires_api_key: bool


PROVIDER_OPTIONS = [
    ProviderOption(DEFAULT_PROVIDER, "Ollama", DEFAULT_MODEL, False),
    ProviderOption("openai", "OpenAI", OPENAI_DEFAULT_MODEL, True),
    ProviderOption("anthropic", "Claude/Anthropic", ANTHROPIC_DEFAULT_MODEL, True),
]

AUTO_MODEL_VALUES = {"", "auto", "detect", "auto-detect", "ollama/auto", "ollama/detect"}
LOCAL_QWEN_CODER_MODEL = "qwen2.5-coder"
OLLAMA_MODEL_PREFERENCES = [
    LOCAL_QWEN_CODER_MODEL,
    "qwen2.5-coder:latest",
    "qwen2.5-coder:7b",
    "qwen3:4b",
    "qwen3",
    "qwen3:latest",
    "llama3.1",
    "llama3.1:latest",
    "llama3",
    "llama3:latest",
]


def normalize_provider(provider: str | None) -> str:
    cleaned = (provider or DEFAULT_PROVIDER).strip().lower()
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


def clean_ollama_model_name(model: str | None) -> str:
    return (model or "").strip().removeprefix("ollama/")


def is_auto_model_request(model: str | None) -> bool:
    return (model or "").strip().lower() in AUTO_MODEL_VALUES


def select_preferred_ollama_model(models: list[str]) -> str | None:
    if not models:
        return None
    model_set = set(models)
    for preferred in OLLAMA_MODEL_PREFERENCES:
        if preferred in model_set:
            return preferred
        if ":" not in preferred and f"{preferred}:latest" in model_set:
            return f"{preferred}:latest"
    return models[0]


def get_ollama_models() -> list[str]:
    from llm_providers.langchain_client import list_ollama_models

    settings = get_settings()
    return list_ollama_models(settings.ollama_base_url)


def has_configured_secret(value: str | None) -> bool:
    return bool(value and value.strip())


def api_key_configured(provider: str | None) -> bool:
    settings = get_settings()
    normalized_provider = normalize_provider(provider)
    if normalized_provider == "openai":
        return has_configured_secret(settings.openai_api_key)
    if normalized_provider == "anthropic":
        return has_configured_secret(settings.anthropic_api_key)
    return False


def cloud_provider_status() -> dict[str, bool]:
    return {
        "openai_configured": api_key_configured("openai"),
        "anthropic_configured": api_key_configured("anthropic"),
    }


def resolve_model(provider: str, model: str | None) -> str:
    """Resolve the selected model, auto-detecting a local Ollama model when possible."""

    settings = get_settings()
    selected = (model or "").strip()
    if provider != "ollama":
        return selected or settings.llm_model

    installed_models = get_ollama_models()
    if not installed_models:
        raise ProviderModelNotFoundError(
            "Ollama is running, but no local models are installed. "
            "Run `ollama pull qwen2.5-coder`; Mission Control will detect it automatically."
        )
    requested = clean_ollama_model_name(selected)
    default_model = clean_ollama_model_name(settings.llm_model)
    default_missing = default_model and not LangChainModelMatcher.is_installed(default_model, installed_models)

    if is_auto_model_request(selected) or not requested or (requested == default_model and default_missing):
        detected = select_preferred_ollama_model(installed_models)
        if detected:
            return detected

    if LangChainModelMatcher.is_installed(requested, installed_models):
        return requested

    available = ", ".join(installed_models) if installed_models else "none"
    raise ProviderModelNotFoundError(
        f"Ollama is running, but model '{requested}' is not installed. "
        f"Available local models: {available}. Use auto-detect or select one of the installed models."
    )


class LangChainModelMatcher:
    @staticmethod
    def is_installed(selected_model: str, installed_models: list[str]) -> bool:
        if selected_model in installed_models:
            return True
        if ":" not in selected_model and f"{selected_model}:latest" in installed_models:
            return True
        return False


def ollama_discovery_status() -> dict[str, str | bool | list[str] | None]:
    try:
        models = get_ollama_models()
    except ProviderConnectionError:
        return {
            "ollama_running": False,
            "ollama_models": [],
            "detected_model": None,
            "message": "Ollama is not running. Start it with `ollama serve`; Mission Control will auto-detect installed models.",
        }

    detected = select_preferred_ollama_model(models)
    if detected:
        message = f"Detected local Ollama model: {detected}"
    else:
        message = "Ollama is running, but no local models are installed. Try `ollama pull qwen2.5-coder`."
    return {
        "ollama_running": True,
        "ollama_models": models,
        "detected_model": detected,
        "message": message,
    }


def model_recommendations(discovery: dict[str, str | bool | list[str] | None]) -> list[dict[str, str]]:
    recommendations: list[dict[str, str]] = []
    detected_model = discovery.get("detected_model")
    if isinstance(detected_model, str) and detected_model:
        recommendations.append(
            {
                "provider": "ollama",
                "model": detected_model,
                "label": "Detected local model",
                "reason": "Best default because it is already installed and running locally.",
            }
        )

    recommendations.append(
        {
            "provider": "ollama",
            "model": LOCAL_QWEN_CODER_MODEL,
            "label": "Local coding model",
            "reason": "Recommended local coding model. Pull with `ollama pull qwen2.5-coder`.",
        }
    )
    recommendations.append(
        {
            "provider": "openai",
            "model": OPENAI_DEFAULT_MODEL,
            "label": "OpenAI cloud coding model",
            "reason": "Recommended cloud option for coding and agentic workflows when OPENAI_API_KEY is configured.",
        }
    )
    recommendations.append(
        {
            "provider": "anthropic",
            "model": ANTHROPIC_DEFAULT_MODEL,
            "label": "Anthropic cloud model",
            "reason": "Alternative cloud option when ANTHROPIC_API_KEY is configured.",
        }
    )
    return recommendations


def suggested_provider_model(discovery: dict[str, str | bool | list[str] | None]) -> tuple[str, str]:
    detected_model = discovery.get("detected_model")
    if isinstance(detected_model, str) and detected_model:
        return "ollama", detected_model
    if api_key_configured("openai"):
        return "openai", OPENAI_DEFAULT_MODEL
    if api_key_configured("anthropic"):
        return "anthropic", ANTHROPIC_DEFAULT_MODEL
    return "ollama", "auto"


def build_chat_provider(provider: str | None = None, model: str | None = None):
    from llm_providers.langchain_client import LangChainChatProvider

    settings = get_settings()
    normalized_provider = normalize_provider(provider or settings.llm_provider)
    selected_model = model or settings.llm_model
    if normalized_provider == "ollama":
        selected_model = resolve_model(normalized_provider, selected_model)
    normalized_model = normalize_model_name(normalized_provider, selected_model)
    api_base = settings.ollama_base_url if normalized_provider == "ollama" else None
    return LangChainChatProvider(provider=normalized_provider, model=normalized_model, api_base=api_base)


def build_chat_model(provider: str | None = None, model: str | None = None):
    chat_provider = build_chat_provider(provider, model)
    chat_provider.validate()
    return chat_provider.chat_model


def provider_options() -> list[dict[str, str | bool]]:
    options: list[dict[str, str | bool]] = []
    for option in PROVIDER_OPTIONS:
        options.append(
            {
                **option.__dict__,
                "api_key_configured": api_key_configured(option.id) if option.requires_api_key else False,
            }
        )
    return options
