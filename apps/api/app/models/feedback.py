from uuid import UUID

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import JsonDict, UUIDType


class UserFeedback(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_feedback"
    __table_args__ = (Index("ix_user_feedback_user_status", "user_id", "status"),)

    user_id: Mapped[UUID] = mapped_column(UUIDType, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    feature: Mapped[str] = mapped_column(String(100), nullable=False)
    feedback_type: Mapped[str] = mapped_column(String(30), nullable=False)
    severity: Mapped[str] = mapped_column(String(30), default="medium", nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="open", nullable=False)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JsonDict, default=dict, nullable=False)
