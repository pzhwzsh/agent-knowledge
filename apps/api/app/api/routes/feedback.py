from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.feedback import UserFeedbackCreate, UserFeedbackResponse, UserFeedbackUpdate
from app.services.audit import AuditService
from app.services.feedback import UserFeedbackService

router = APIRouter()


@router.post("", response_model=UserFeedbackResponse, status_code=status.HTTP_201_CREATED)
def create_feedback(
    payload: UserFeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return UserFeedbackService(db).create(current_user.id, payload)


@router.get("", response_model=list[UserFeedbackResponse])
def list_feedback(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    return UserFeedbackService(db).list_for_user(current_user.id, limit=limit, offset=offset)


@router.get("/admin/all", response_model=list[UserFeedbackResponse])
def list_all_feedback(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    AuditService(db).record(user_id=current_user.id, action="feedback_admin_list", resource_type="user_feedback")
    return UserFeedbackService(db).list_all(status_filter=status_filter, limit=limit, offset=offset)


@router.patch("/admin/{feedback_id}", response_model=UserFeedbackResponse)
def update_feedback_status(
    feedback_id: UUID,
    payload: UserFeedbackUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    updated = UserFeedbackService(db).update_status(feedback_id, payload)
    AuditService(db).record(
        user_id=current_user.id,
        action="feedback_status_update",
        resource_type="user_feedback",
        resource_id=str(feedback_id),
        metadata_json={"status": payload.status},
    )
    return updated
