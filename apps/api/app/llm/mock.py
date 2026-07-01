from collections.abc import Sequence

from app.llm.base import ChatModel, EmbeddingModel


class MockChatModel(ChatModel):
    def complete(self, messages: Sequence[dict[str, str]]) -> str:
        last_message = messages[-1]["content"] if messages else ""
        return f"Mock response for: {last_message[:120]}"


class MockEmbeddingModel(EmbeddingModel):
    def __init__(self, dimensions: int = 1536) -> None:
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        seed = sum(ord(char) for char in text) or 1
        return [float((seed + index) % 100) / 100 for index in range(self.dimensions)]
