from app.core.config import Settings, get_settings
from app.llm.base import ChatModel, EmbeddingModel
from app.llm.errors import LLMConfigurationError
from app.llm.mock import MockChatModel, MockEmbeddingModel
from app.llm.openai_compatible import (
    OpenAICompatibleChatModel,
    OpenAICompatibleClient,
    OpenAICompatibleEmbeddingModel,
)

DEFAULT_BASE_URLS = {
    "deepseek": "https://api.deepseek.com/v1",
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
}


def _provider_settings(settings: Settings) -> tuple[str, str, str]:
    provider = settings.llm_provider.lower()
    if provider == "mock":
        return provider, "", ""
    base_url = settings.llm_base_url or DEFAULT_BASE_URLS.get(provider)
    if not base_url:
        raise LLMConfigurationError("LLM_BASE_URL is required for the selected provider")
    if not settings.llm_api_key:
        raise LLMConfigurationError("LLM_API_KEY is required for the selected provider")
    return provider, str(base_url), settings.llm_api_key


def get_chat_model(settings: Settings | None = None) -> ChatModel:
    resolved = settings or get_settings()
    provider, base_url, api_key = _provider_settings(resolved)
    if provider == "mock":
        return MockChatModel()
    if provider in {"openai_compatible", "deepseek", "qwen"}:
        if not resolved.llm_model:
            raise LLMConfigurationError("LLM_MODEL is required for chat completions")
        client = OpenAICompatibleClient(base_url=base_url, api_key=api_key)
        return OpenAICompatibleChatModel(client=client, model=resolved.llm_model)
    raise LLMConfigurationError(f"Unsupported LLM provider: {resolved.llm_provider}")


def get_embedding_model(settings: Settings | None = None) -> EmbeddingModel:
    resolved = settings or get_settings()
    provider, base_url, api_key = _provider_settings(resolved)
    if provider == "mock":
        return MockEmbeddingModel()
    if provider in {"openai_compatible", "deepseek", "qwen"}:
        if not resolved.embedding_model:
            raise LLMConfigurationError("EMBEDDING_MODEL is required for embeddings")
        client = OpenAICompatibleClient(base_url=base_url, api_key=api_key)
        return OpenAICompatibleEmbeddingModel(client=client, model=resolved.embedding_model)
    raise LLMConfigurationError(f"Unsupported LLM provider: {resolved.llm_provider}")
