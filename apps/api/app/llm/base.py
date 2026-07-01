from abc import ABC, abstractmethod
from collections.abc import Sequence


class ChatModel(ABC):
    @abstractmethod
    def complete(self, messages: Sequence[dict[str, str]]) -> str:
        raise NotImplementedError


class EmbeddingModel(ABC):
    @abstractmethod
    def embed(self, text: str) -> list[float]:
        raise NotImplementedError


class PromptTemplate:
    def __init__(self, template: str) -> None:
        self.template = template

    def render(self, **kwargs: object) -> str:
        return self.template.format(**kwargs)


class TokenUsageTracker:
    def count(self, text: str) -> int:
        return len(text.split())
