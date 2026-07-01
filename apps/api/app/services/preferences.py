from uuid import UUID

from sqlalchemy.orm import Session

from app.models.preference import UserPreference
from app.repositories.preferences import PreferenceRepository
from app.schemas.preferences import PreferenceUpdateRequest


class PreferenceService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.preferences = PreferenceRepository(db)

    def get_for_user(self, user_id: UUID) -> UserPreference:
        preference = self.preferences.get_by_user_id(user_id)
        if preference is None:
            preference = self.preferences.create_default(user_id)
            self.db.commit()
            self.db.refresh(preference)
        return preference

    def update_for_user(self, user_id: UUID, payload: PreferenceUpdateRequest) -> UserPreference:
        preference = self.get_for_user(user_id)
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(preference, field, value)
        self.db.add(preference)
        self.db.commit()
        self.db.refresh(preference)
        return preference
