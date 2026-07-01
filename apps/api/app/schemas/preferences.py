from datetime import time
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import DEFAULT_ENABLED_CATEGORIES


class PreferenceResponse(BaseModel):
    id: UUID
    user_id: UUID
    interests: list[str]
    negative_interests: list[str]
    enabled_categories: list[str]
    push_channel: str
    push_email: EmailStr | None
    dingtalk_webhook: str | None
    push_time: time
    daily_limit: int
    language_preferences: dict[str, object]

    model_config = {"from_attributes": True}


class PreferenceUpdateRequest(BaseModel):
    interests: list[str] | None = None
    negative_interests: list[str] | None = None
    enabled_categories: list[str] | None = None
    push_channel: str | None = None
    push_email: EmailStr | None = None
    dingtalk_webhook: str | None = None
    push_time: time | None = None
    daily_limit: int | None = Field(default=None, ge=1, le=100)
    language_preferences: dict[str, object] | None = None


class PreferenceDefaults(BaseModel):
    interests: list[str] = Field(default_factory=list)
    negative_interests: list[str] = Field(default_factory=list)
    enabled_categories: list[str] = Field(default_factory=lambda: DEFAULT_ENABLED_CATEGORIES.copy())
    push_channel: str = "in_app"
    daily_limit: int = 10
