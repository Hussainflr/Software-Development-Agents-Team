from llm_providers.factory import normalize_model_name, normalize_provider


def test_normalize_provider_accepts_claude_alias():
    assert normalize_provider("claude") == "anthropic"


def test_normalize_model_name_prefixes_ollama():
    assert normalize_model_name("ollama", "qwen3:4b") == "ollama/qwen3:4b"

