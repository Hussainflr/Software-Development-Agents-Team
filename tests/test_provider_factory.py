from llm_providers.factory import normalize_model_name, normalize_provider, select_preferred_ollama_model
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
