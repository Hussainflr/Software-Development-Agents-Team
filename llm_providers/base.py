class LLMError(RuntimeError):
    """Base error for provider failures."""


class ProviderConfigurationError(LLMError):
    """Raised when a provider is selected but not configured."""


class ProviderConnectionError(LLMError):
    """Raised when a local or remote provider cannot be reached."""

