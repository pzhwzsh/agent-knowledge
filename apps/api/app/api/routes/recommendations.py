from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.recommendation import (
    RecommendationGenerateRequest,
    RecommendationResponse,
    RecommendationSaveResponse,
)
from app.services.recommendations import RecommendationService

router = APIRouter()


@router.get("", response_model=list[RecommendationResponse])
def list_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    return RecommendationService(db).list_recommendations(
        current_user.id,
        status_filter=status_filter,
        limit=limit,
        offset=offset,
    )


@router.post("/generate", response_model=RecommendationResponse)
def generate_recommendation(
    payload: RecommendationGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return RecommendationService(db).generate_for_content(current_user.id, payload.content_id)


@router.post("/{recommendation_id}/ignore", response_model=RecommendationResponse)
def ignore_recommendation(
    recommendation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return RecommendationService(db).ignore(current_user.id, recommendation_id)


@router.post("/{recommendation_id}/dislike", response_model=RecommendationResponse)
def dislike_recommendation(
    recommendation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return RecommendationService(db).dislike(current_user.id, recommendation_id)


@router.post("/{recommendation_id}/save", response_model=RecommendationSaveResponse)
def save_recommendation(
    recommendation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return RecommendationService(db).save(current_user.id, recommendation_id)
