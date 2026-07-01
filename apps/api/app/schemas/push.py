from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class PushLogResponse(BaseModel):
    id: UUID
    user_id: UUID
    channel: str
    status: str
    message: str | None
    metadata_json: dict[str, Any]
    sent_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PushTriggerResponse(BaseModel):
    push_log_id: str
    channel: str
    status: str
    message: str
    recommendation_count: int
