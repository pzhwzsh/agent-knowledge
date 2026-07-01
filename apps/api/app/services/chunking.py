from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    index: int
    content: str
    metadata: dict[str, object]


class TextChunker:
    def __init__(self, *, chunk_size: int = 1000, overlap: int = 150) -> None:
        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def split(self, text: str, *, metadata: dict[str, object] | None = None) -> list[TextChunk]:
        normalized = " ".join(text.split())
        if not normalized:
            return []
        chunks: list[TextChunk] = []
        start = 0
        base_metadata = metadata or {}
        while start < len(normalized):
            end = min(start + self.chunk_size, len(normalized))
            chunk_text = normalized[start:end]
            chunks.append(
                TextChunk(
                    index=len(chunks),
                    content=chunk_text,
                    metadata={**base_metadata, "start": start, "end": end},
                )
            )
            if end == len(normalized):
                break
            start = max(end - self.overlap, 0)
        return chunks
