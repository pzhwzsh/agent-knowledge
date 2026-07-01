from datetime import UTC, datetime
from hashlib import sha256

from app.collectors.web import WebPageCollector
from app.models.enums import SourceType
from app.schemas.content import ContentCreate
from app.schemas.ingestion import IngestionJobCreate


class ContentBuilder:
    def __init__(self, collector: WebPageCollector | None = None) -> None:
        self.collector = collector or WebPageCollector()

    def build(self, payload: IngestionJobCreate) -> ContentCreate:
        if payload.input_type == "text":
            text = payload.input_value.strip()
            return ContentCreate(
                title=text[:80] or "Untitled text",
                source_type=SourceType.TEXT.value,
                raw_text=text,
                content_hash=_hash_text(text),
                fetched_at=datetime.now(UTC),
            )
        page = self.collector.fetch_page(payload.input_value)
        text = page["text"]
        return ContentCreate(
            url=payload.input_value,
            canonical_url=page["url"],
            title=page["title"],
            source_type=SourceType.ARTICLE.value,
            raw_text=text,
            content_hash=_hash_text(text),
            fetched_at=datetime.fromisoformat(page["fetched_at"]),
        )


def _hash_text(text: str) -> str:
    return sha256(text.strip().encode("utf-8")).hexdigest()
