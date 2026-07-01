from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Float, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import StringList, UUIDType

if TYPE_CHECKING:
    from app.models.content import Content



class Recommendation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "recommendations"
    __table_args__ = (Index("ix_recommendations_user_status", "user_id", "status"),)

    user_id: Mapped[UUID] = mapped_column(UUIDType, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    content_id: Mapped[UUID] = mapped_column(UUIDType, ForeignKey("contents.id", ondelete="CASCADE"), index=True, nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    reason: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[list[str]] = mapped_column(StringList, default=list, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)

    content: Mapped["Content"] = relationship(back_populates="recommendations")
