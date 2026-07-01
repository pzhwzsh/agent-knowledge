import httpx
import pytest

from app.core.config import Settings
from app.llm.errors import LLMConfigurationError, LLMProviderError
from app.llm.mock import MockChatModel, MockEmbeddingModel
from app.llm.openai_compatible import (
    OpenAICompatibleChatModel,
    OpenAICompatibleClient,
    OpenAICompatibleEmbeddingModel,
)
from app.llm.providers import get_chat_model, get_embedding_model


def make_settings(**overrides: object) -> Settings:
    values = {
        "app_secret_key": "test-secret-key",
        "database_url": "sqlite://",
        "llm_provider": "mock",
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


def test_mock_provider_selection() -> None:
    settings = make_settings(llm_provider="mock")

    assert isinstance(get_chat_model(settings), MockChatModel)
    assert isinstance(get_embedding_model(settings), MockEmbeddingModel)


def test_openai_compatible_chat_model_parses_content() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/chat/completions"
        return httpx.Response(200, json={"choices": [{"message": {"content": "hello"}}]})

    client = OpenAICompatibleClient(
        base_url="https://example.test/v1",
        api_key="key",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    model = OpenAICompatibleChatModel(client=client, model="chat")

    assert model.complete([{"role": "user", "content": "Hi"}]) == "hello"


def test_openai_compatible_embedding_model_parses_vector() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/embeddings"
        return httpx.Response(200, json={"data": [{"embedding": [0, 1.5, 2]}]})

    client = OpenAICompatibleClient(
        base_url="https://example.test/v1",
        api_key="key",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    model = OpenAICompatibleEmbeddingModel(client=client, model="embedding")

    assert model.embed("hello") == [0.0, 1.5, 2.0]


def test_provider_http_error_is_explicit() -> None:
    client = OpenAICompatibleClient(
        base_url="https://example.test/v1",
        api_key="key",
        client=httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(500))),
    )
    model = OpenAICompatibleChatModel(client=client, model="chat")

    with pytest.raises(LLMProviderError):
        model.complete([{"role": "user", "content": "Hi"}])


def test_openai_compatible_requires_api_key() -> None:
    settings = make_settings(
        llm_provider="openai_compatible",
        llm_base_url="https://example.test/v1",
        llm_model="chat",
    )

    with pytest.raises(LLMConfigurationError, match="LLM_API_KEY"):
        get_chat_model(settings)


def test_deepseek_uses_default_base_url_but_requires_model() -> None:
    settings = make_settings(llm_provider="deepseek", llm_api_key="key")

    with pytest.raises(LLMConfigurationError, match="LLM_MODEL"):
        get_chat_model(settings)
