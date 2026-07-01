from abc import ABC, abstractmethod


class Collector(ABC):
    @abstractmethod
    def fetch(self, source: str) -> str:
        raise NotImplementedError
