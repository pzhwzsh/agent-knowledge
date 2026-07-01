from collections.abc import Sequence
from typing import Any

import httpx

from app.llm.base import ChatModel, EmbeddingModel
from app.llm.errors import LLMProviderError


class OpenAICompatibleClient:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        timeout: float = 30.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client = client or httpx.Client(timeout=timeout)

    def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self._client.post(
                f"{self.base_url}{path}",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as exc:
            raise LLMProviderError(
                f"Model provider returned HTTP {exc.response.status_code}"
            ) from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise LLMProviderError("Model provider request failed") from exc
        if not isinstance(data, dict):
            raise LLMProviderError("Model provider returned a non-object response")
        return data


class OpenAICompatibleChatModel(ChatModel):
    def __init__(self, *, client: OpenAICompatibleClient, model: str) -> None:
        self.client = client
        self.model = model

    def complete(self, messages: Sequence[dict[str, str]]) -> str:
        data = self.client.post(
            "/chat/completions",
            {"model": self.model, "messages": list(messages)},
        )
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMProviderError("Chat completion response missing message content") from exc
        if not isinstance(content, str):
            raise LLMProviderError("Chat completion content must be a string")
        return content


class OpenAICompatibleEmbeddingModel(EmbeddingModel):
    def __init__(self, *, client: OpenAICompatibleClient, model: str) -> None:
        self.client = client
        self.model = model

    def embed(self, text: str) -> list[float]:
        data = self.client.post(
            "/embeddings",
            {"model": self.model, "input": text},
        )
        try:
            embedding = data["data"][0]["embedding"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMProviderError("Embedding response missing vector data") from exc
        if not isinstance(embedding, list) or not all(isinstance(value, int | float) for value in embedding):
            raise LLMProviderError("Embedding response must be a numeric list")
        return [float(value) for value in embedding]
