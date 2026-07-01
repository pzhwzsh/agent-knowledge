from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.content import Content
from app.schemas.content import ContentCreate


class ContentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, content_id: UUID) -> Content | None:
        return self.db.get(Content, content_id)

    def get_by_hash(self, content_hash: str) -> Content | None:
        return self.db.scalar(select(Content).where(Content.content_hash == content_hash))

    def get_by_canonical_url(self, canonical_url: str) -> Content | None:
        return self.db.scalar(select(Content).where(Content.canonical_url == canonical_url))

    def get_existing(self, *, content_hash: str | None, canonical_url: str | None) -> Content | None:
        if content_hash:
            content = self.get_by_hash(content_hash)
            if content is not None:
                return content
        if canonical_url:
            return self.get_by_canonical_url(canonical_url)
        return None

    def create(self, payload: ContentCreate) -> Content:
        content = Content(**payload.model_dump())
        self.db.add(content)
        self.db.flush()
        return content

    def get_or_create(self, payload: ContentCreate) -> Content:
        existing = self.get_existing(
            content_hash=payload.content_hash,
            canonical_url=payload.canonical_url,
        )
        if existing is not None:
            return existing
        return self.create(payload)
