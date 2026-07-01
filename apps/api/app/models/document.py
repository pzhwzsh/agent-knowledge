from __future__ import annotations

from typing import Any, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import EmbeddingVector, JsonDict, StringList, UUIDType

if TYPE_CHECKING:
    from app.models.content import Content



class Document(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint("user_id", "content_id", name="uq_documents_user_content"),
        Index("ix_documents_user_category", "user_id", "category"),
    )

    user_id: Mapped[UUID] = mapped_column(UUIDType, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    content_id: Mapped[UUID | None] = mapped_column(UUIDType, ForeignKey("contents.id", ondelete="SET NULL"), index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(1000))
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    long_summary: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[list[str]] = mapped_column(StringList, default=list, nullable=False)

    content: Mapped["Content | None"] = relationship(back_populates="documents")
    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "document_chunks"
    __table_args__ = (
        Index("ix_document_chunks_user_document", "user_id", "document_id"),
    )

    user_id: Mapped[UUID] = mapped_column(UUIDType, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    document_id: Mapped[UUID] = mapped_column(UUIDType, ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(EmbeddingVector)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JsonDict, default=dict, nullable=False)

    document: Mapped[Document] = relationship(back_populates="chunks")
