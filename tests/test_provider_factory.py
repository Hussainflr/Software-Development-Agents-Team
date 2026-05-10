from types import SimpleNamespace

from llm_providers import factory
from llm_providers.factory import (
    api_key_configured,
    normalize_model_name,
    normalize_provider,
    provider_options,
    select_preferred_ollama_model,
    suggested_provider_model,
)
from llm_providers.langchain_client import LangChainChatProvider


def test_normalize_provider_accepts_claude_alias():
    assert normalize_provider("claude") == "anthropic"


def test_normalize_model_name_prefixes_ollama():
    assert normalize_model_name("ollama", "qwen2.5-coder") == "ollama/qwen2.5-coder"


def test_select_preferred_ollama_model_prefers_local_coder_model():
    assert select_preferred_ollama_model(["llama3.1:latest", "qwen3:4b"]) == "qwen3:4b"


def test_select_preferred_ollama_model_falls_back_to_first_installed_model():
    assert select_preferred_ollama_model(["mistral:latest", "phi4:latest"]) == "mistral:latest"


def test_ollama_model_matching_accepts_latest_tag():
    assert LangChainChatProvider._model_is_installed("qwen2.5-coder", ["qwen2.5-coder:latest"])


def test_ollama_model_matching_rejects_different_model():
    assert not LangChainChatProvider._model_is_installed("qwen2.5-coder", ["qwen3:4b"])


def test_api_key_detection_uses_loaded_settings(monkeypatch):
    settings = SimpleNamespace(openai_api_key="sk-test", anthropic_api_key=" ")
    monkeypatch.setattr(factory, "get_settings", lambda: settings)

    assert api_key_configured("openai")
    assert not api_key_configured("anthropic")


def test_provider_options_include_safe_api_key_status(monkeypatch):
    settings = SimpleNamespace(openai_api_key="sk-test", anthropic_api_key=None)
    monkeypatch.setattr(factory, "get_settings", lambda: settings)

    options = {item["id"]: item for item in provider_options()}

    assert options["openai"]["api_key_configured"] is True
    assert options["anthropic"]["api_key_configured"] is False


def test_suggested_provider_uses_configured_anthropic_when_ollama_missing(monkeypatch):
    settings = SimpleNamespace(openai_api_key="", anthropic_api_key="anthropic-test")
    monkeypatch.setattr(factory, "get_settings", lambda: settings)

    provider, model = suggested_provider_model({"detected_model": None})

    assert provider == "anthropic"
    assert model.startswith("claude")
