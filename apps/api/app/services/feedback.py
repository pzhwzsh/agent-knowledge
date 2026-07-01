from uuid import UUID

from sqlalchemy.orm import Session

from app.models.feedback import UserFeedback
from app.repositories.feedback import UserFeedbackRepository
from app.schemas.feedback import UserFeedbackCreate


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
