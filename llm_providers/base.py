from typing import Protocol, TypedDict


class ChatMessage(TypedDict):
    role: str
    content: str


class LLMError(RuntimeError):
    """Base error for provider failures."""


class ProviderConfigurationError(LLMError):
    """Raised when a provider is selected but not configured."""


class ProviderConnectionError(LLMError):
    """Raised when a local or remote provider cannot be reached."""


class LLMClient(Protocol):
    provider: str
    model: str

    def generate(self, messages: list[ChatMessage], temperature: float = 0.2) -> str:
        """Return assistant text for a chat-style prompt."""

