class LLMError(RuntimeError):
    """Base error for model provider failures."""


class LLMConfigurationError(LLMError):
    """Raised when a provider is selected without required configuration."""


class LLMProviderError(LLMError):
    """Raised when a model provider returns an invalid or failed response."""
