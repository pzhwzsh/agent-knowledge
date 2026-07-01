from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.feedback import UserFeedbackCreate, UserFeedbackResponse
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
