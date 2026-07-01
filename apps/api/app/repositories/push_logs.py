from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.logs import PushLog


class PushLogRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        user_id: UUID,
        channel: str,
        status: str,
        message: str | None,
        metadata_json: dict[str, Any] | None = None,
        sent: bool = False,
    ) -> PushLog:
        log = PushLog(
            user_id=user_id,
            channel=channel,
            status=status,
            message=message,
            metadata_json=metadata_json or {},
            sent_at=datetime.now(UTC) if sent else None,
        )
        self.db.add(log)
        self.db.flush()
        return log

    def list_for_user(self, user_id: UUID, *, limit: int = 50, offset: int = 0) -> list[PushLog]:
        statement = (
            select(PushLog)
            .where(PushLog.user_id == user_id)
            .order_by(PushLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.scalars(statement))
