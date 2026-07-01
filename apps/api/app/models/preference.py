from __future__ import annotations

from datetime import time
from typing import Any, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import JsonDict, StringList, UUIDType
from app.models.enums import DEFAULT_ENABLED_CATEGORIES

if TYPE_CHECKING:
    from app.models.user import User



class UserPreference(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_preferences"

    user_id: Mapped[UUID] = mapped_column(UUIDType, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    interests: Mapped[list[str]] = mapped_column(StringList, default=list, nullable=False)
    negative_interests: Mapped[list[str]] = mapped_column(StringList, default=list, nullable=False)
    enabled_categories: Mapped[list[str]] = mapped_column(StringList, default=lambda: DEFAULT_ENABLED_CATEGORIES.copy(), nullable=False)
    push_channel: Mapped[str] = mapped_column(String(30), default="in_app", nullable=False)
    push_email: Mapped[str | None] = mapped_column(String(255))
    dingtalk_webhook: Mapped[str | None] = mapped_column(String(500))
    push_time: Mapped[time] = mapped_column(Time, default=time(hour=9), nullable=False)
    daily_limit: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    language_preferences: Mapped[dict[str, Any]] = mapped_column(JsonDict, default=dict, nullable=False)

    user: Mapped["User"] = relationship(back_populates="preferences")
