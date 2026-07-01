from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.agents.recommender import RecommenderAgent
from app.models.enums import RecommendationStatus
from app.models.recommendation import Recommendation
from app.repositories.contents import ContentRepository
from app.repositories.preferences import PreferenceRepository
from app.repositories.recommendations import RecommendationRepository
from app.schemas.document import DocumentCreateFromContent
from app.schemas.recommendation import RecommendationCreate, RecommendationSaveResponse
from app.services.document_ingestion import DocumentIngestionService


class RecommendationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.recommendations = RecommendationRepository(db)
        self.contents = ContentRepository(db)
        self.preferences = PreferenceRepository(db)
        self.agent = RecommenderAgent()

    def list_recommendations(
        self,
        user_id: UUID,
        *,
        status_filter: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Recommendation]:
        return self.recommendations.list_for_user(
            user_id,
            status=status_filter,
            limit=limit,
            offset=offset,
        )

    def create_recommendation(self, user_id: UUID, payload: RecommendationCreate) -> Recommendation:
        existing = self.recommendations.get_by_user_content(user_id, payload.content_id)
        if existing is not None:
            return existing
        recommendation = self.recommendations.create_for_user(user_id, payload)
        self.db.commit()
        self.db.refresh(recommendation)
        return recommendation

    def generate_for_content(self, user_id: UUID, content_id: UUID) -> Recommendation:
        content = self.contents.get_by_id(content_id)
        if content is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")
        preference = self.preferences.get_by_user_id(user_id)
        decision = self.agent.run(
            {
                "title": content.title or "",
                "text": content.raw_text or "",
                "category": "other",
                "interests": preference.interests if preference else [],
                "negative_interests": preference.negative_interests if preference else [],
                "enabled_categories": preference.enabled_categories if preference else [],
            }
        )
        return self.create_recommendation(
            user_id,
            RecommendationCreate(
                content_id=content.id,
                score=float(decision.score),
                category=decision.category,
                summary=(content.raw_text or content.title or "")[:300],
                reason=decision.reason,
                tags=decision.matched_interests,
                status=RecommendationStatus.PENDING.value,
            ),
        )

    def set_status(self, user_id: UUID, recommendation_id: UUID, new_status: RecommendationStatus) -> Recommendation:
        recommendation = self.recommendations.update_status_for_user(
            user_id,
            recommendation_id,
            new_status.value,
        )
        if recommendation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")
        self.db.commit()
        self.db.refresh(recommendation)
        return recommendation

    def ignore(self, user_id: UUID, recommendation_id: UUID) -> Recommendation:
        return self.set_status(user_id, recommendation_id, RecommendationStatus.IGNORED)

    def dislike(self, user_id: UUID, recommendation_id: UUID) -> Recommendation:
        return self.set_status(user_id, recommendation_id, RecommendationStatus.DISLIKED)

    def save(self, user_id: UUID, recommendation_id: UUID) -> RecommendationSaveResponse:
        recommendation = self.recommendations.get_for_user(user_id, recommendation_id)
        if recommendation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")
        document = DocumentIngestionService(self.db).create_from_content(
            user_id,
            DocumentCreateFromContent(
                content_id=recommendation.content_id,
                category=recommendation.category,
                summary=recommendation.summary,
                tags=recommendation.tags,
            ),
        )
        recommendation = self.set_status(user_id, recommendation_id, RecommendationStatus.SAVED)
        return RecommendationSaveResponse(recommendation=recommendation, document=document)
