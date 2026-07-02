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

    def list_all(self, *, status: str | None = None, limit: int = 100, offset: int = 0) -> list[UserFeedback]:
        statement = select(UserFeedback)
        if status is not None:
            statement = statement.where(UserFeedback.status == status)
        statement = statement.order_by(UserFeedback.created_at.desc()).limit(limit).offset(offset)
        return list(self.db.scalars(statement))

    def get_by_id(self, feedback_id: UUID) -> UserFeedback | None:
        return self.db.get(UserFeedback, feedback_id)

    def update_status(self, feedback: UserFeedback, status: str, metadata_json: dict[str, object] | None = None) -> UserFeedback:
        feedback.status = status
        if metadata_json is not None:
            feedback.metadata_json = {**feedback.metadata_json, **metadata_json}
        self.db.add(feedback)
        self.db.flush()
        return feedback
