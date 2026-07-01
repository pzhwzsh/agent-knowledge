from __future__ import annotations

from datetime import datetime
from typing import Any, TYPE_CHECKING

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import JsonDict

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.recommendation import Recommendation



class Source(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sources"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str | None] = mapped_column(String(1000))
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JsonDict)


class Content(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "contents"
    __table_args__ = (
        Index("ix_contents_content_hash", "content_hash"),
        Index("ix_contents_canonical_url", "canonical_url"),
    )

    url: Mapped[str | None] = mapped_column(String(1000))
    canonical_url: Mapped[str | None] = mapped_column(String(1000))
    title: Mapped[str | None] = mapped_column(String(500))
    author: Mapped[str | None] = mapped_column(String(255))
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)
    source_name: Mapped[str | None] = mapped_column(String(255))
    raw_text: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str | None] = mapped_column(String(128))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    documents: Mapped[list["Document"]] = relationship(back_populates="content")
    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="content")
