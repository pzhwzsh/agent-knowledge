from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.audit import AuditLogResponse
from app.services.audit import AuditService

router = APIRouter()


@router.get("/logs", response_model=list[AuditLogResponse])
def list_audit_logs(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    user_id: UUID | None = Query(default=None),
    action: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    AuditService(db).record(
        user_id=current_user.id,
        action="audit_log_list",
        resource_type="audit_logs",
        metadata_json={
            "filter_user_id": str(user_id) if user_id else None,
            "filter_action": action,
            "filter_resource_type": resource_type,
        },
    )
    return AuditService(db).list_all(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        limit=limit,
        offset=offset,
    )
