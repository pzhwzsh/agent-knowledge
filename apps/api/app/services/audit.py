from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.logs import AuditLog
from app.repositories.audit_logs import AuditLogRepository


class AuditService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.logs = AuditLogRepository(db)

    def record(
        self,
        *,
        user_id: UUID,
        action: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> AuditLog:
        log = self.logs.create(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata_json=metadata_json,
        )
        self.db.commit()
        self.db.refresh(log)
        return log
