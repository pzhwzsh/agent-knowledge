from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.push_logs import PushLogRepository
from app.schemas.push import PushLogResponse, PushTriggerResponse
from app.services.push import RecommendationPushService

router = APIRouter()


@router.get("/logs", response_model=list[PushLogResponse])
def list_push_logs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    return PushLogRepository(db).list_for_user(current_user.id, limit=limit, offset=offset)


@router.post("/daily", response_model=PushTriggerResponse)
def trigger_daily_push(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return RecommendationPushService(db).push_daily_recommendations(current_user.id)
