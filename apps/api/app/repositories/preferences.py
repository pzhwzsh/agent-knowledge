from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import DEFAULT_ENABLED_CATEGORIES
from app.models.preference import UserPreference


class PreferenceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_user_id(self, user_id: UUID) -> UserPreference | None:
        return self.db.scalar(select(UserPreference).where(UserPreference.user_id == user_id))

    def create_default(self, user_id: UUID) -> UserPreference:
        preference = UserPreference(
            user_id=user_id,
            interests=[],
            negative_interests=[],
            enabled_categories=DEFAULT_ENABLED_CATEGORIES.copy(),
            push_channel="in_app",
            daily_limit=10,
            language_preferences={},
        )
        self.db.add(preference)
        self.db.flush()
        return preference
