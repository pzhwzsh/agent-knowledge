from abc import ABC, abstractmethod
from typing import Generic, TypeVar

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class AgentRunner(ABC, Generic[InputT, OutputT]):
    @abstractmethod
    def run(self, payload: InputT) -> OutputT:
        raise NotImplementedError
