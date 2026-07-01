from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.feedback import UserFeedback
from app.schemas.feedback import UserFeedbackCreate


class UserFeedbackRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_for_user(self, user_id: UUID, payload: UserFeedbackCreate) -> UserFeedback:
        feedback = UserFeedback(user_id=user_id, **payload.model_dump())
        self.db.add(feedback)
        self.db.flush()
        return feedback

    def list_for_user(self, user_id: UUID, *, limit: int = 50, offset: int = 0) -> list[UserFeedback]:
        statement = (
            select(UserFeedback)
            .where(UserFeedback.user_id == user_id)
            .order_by(UserFeedback.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.scalars(statement))
