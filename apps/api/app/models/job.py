from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import JsonDict, UUIDType


class IngestionJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ingestion_jobs"
    __table_args__ = (Index("ix_ingestion_jobs_user_status", "user_id", "status"),)

    user_id: Mapped[UUID] = mapped_column(UUIDType, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    input_type: Mapped[str] = mapped_column(String(30), nullable=False)
    input_value: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AgentRun(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "agent_runs"
    __table_args__ = (Index("ix_agent_runs_user_agent", "user_id", "agent_name"),)

    user_id: Mapped[UUID] = mapped_column(UUIDType, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    job_id: Mapped[UUID | None] = mapped_column(UUIDType, ForeignKey("ingestion_jobs.id", ondelete="SET NULL"), index=True)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    input_json: Mapped[dict[str, Any]] = mapped_column(JsonDict, default=dict, nullable=False)
    output_json: Mapped[dict[str, Any] | None] = mapped_column(JsonDict)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    token_usage: Mapped[dict[str, Any]] = mapped_column(JsonDict, default=dict, nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
