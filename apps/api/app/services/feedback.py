from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.feedback import UserFeedback
from app.repositories.feedback import UserFeedbackRepository
from app.schemas.feedback import UserFeedbackCreate, UserFeedbackUpdate


class UserFeedbackService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.feedback = UserFeedbackRepository(db)

    def create(self, user_id: UUID, payload: UserFeedbackCreate) -> UserFeedback:
        item = self.feedback.create_for_user(user_id, payload)
        self.db.commit()
        self.db.refresh(item)
        return item

    def list_for_user(self, user_id: UUID, *, limit: int = 50, offset: int = 0) -> list[UserFeedback]:
        return self.feedback.list_for_user(user_id, limit=limit, offset=offset)

    def list_all(self, *, status_filter: str | None = None, limit: int = 100, offset: int = 0) -> list[UserFeedback]:
        return self.feedback.list_all(status=status_filter, limit=limit, offset=offset)

    def update_status(self, feedback_id: UUID, payload: UserFeedbackUpdate) -> UserFeedback:
        item = self.feedback.get_by_id(feedback_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")
        updated = self.feedback.update_status(item, payload.status, payload.metadata_json)
        self.db.commit()
        self.db.refresh(updated)
        return updated
