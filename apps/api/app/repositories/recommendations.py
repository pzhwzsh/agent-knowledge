from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.recommendation import Recommendation
from app.schemas.recommendation import RecommendationCreate


class RecommendationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_user(
        self,
        user_id: UUID,
        *,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Recommendation]:
        statement = select(Recommendation).where(Recommendation.user_id == user_id)
        if status is not None:
            statement = statement.where(Recommendation.status == status)
        statement = statement.order_by(Recommendation.created_at.desc()).limit(limit).offset(offset)
        return list(self.db.scalars(statement))

    def get_for_user(self, user_id: UUID, recommendation_id: UUID) -> Recommendation | None:
        return self.db.scalar(
            select(Recommendation).where(
                Recommendation.user_id == user_id,
                Recommendation.id == recommendation_id,
            )
        )

    def get_by_user_content(self, user_id: UUID, content_id: UUID) -> Recommendation | None:
        return self.db.scalar(
            select(Recommendation).where(
                Recommendation.user_id == user_id,
                Recommendation.content_id == content_id,
            )
        )

    def create_for_user(self, user_id: UUID, payload: RecommendationCreate) -> Recommendation:
        recommendation = Recommendation(user_id=user_id, **payload.model_dump())
        self.db.add(recommendation)
        self.db.flush()
        return recommendation

    def update_status_for_user(
        self,
        user_id: UUID,
        recommendation_id: UUID,
        status: str,
    ) -> Recommendation | None:
        recommendation = self.get_for_user(user_id, recommendation_id)
        if recommendation is None:
            return None
        recommendation.status = status
        self.db.add(recommendation)
        self.db.flush()
        return recommendation

    def list_pending_for_push(self, user_id: UUID, *, limit: int = 10) -> list[Recommendation]:
        statement = (
            select(Recommendation)
            .where(Recommendation.user_id == user_id, Recommendation.status == "pending")
            .order_by(Recommendation.score.desc(), Recommendation.created_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(statement))
