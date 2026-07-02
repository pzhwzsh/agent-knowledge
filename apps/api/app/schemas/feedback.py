from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class UserFeedbackCreate(BaseModel):
    feature: str = Field(min_length=1, max_length=100)
    feedback_type: Literal["bug", "repair", "delete", "idea", "other"] = "other"
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    message: str = Field(min_length=1, max_length=4000)
    metadata_json: dict[str, object] = Field(default_factory=dict)


class UserFeedbackUpdate(BaseModel):
    status: Literal["open", "planned", "in_progress", "resolved", "wont_fix", "deleted"]
    metadata_json: dict[str, object] | None = None


class UserFeedbackResponse(UserFeedbackCreate):
    id: UUID
    user_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
