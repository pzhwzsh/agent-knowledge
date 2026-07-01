from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.content import ContentResponse


class IngestionJobCreate(BaseModel):
    input_type: Literal["url", "text"]
    input_value: str = Field(min_length=1)


class IngestionJobResponse(IngestionJobCreate):
    id: UUID
    user_id: UUID
    status: str
    error_message: str | None
    retry_count: int
    created_at: datetime
    updated_at: datetime
    finished_at: datetime | None

    model_config = {"from_attributes": True}


class IngestionSubmitResponse(BaseModel):
    job: IngestionJobResponse
    content: ContentResponse | None = None
    route: dict[str, object] | None = None
    summary: dict[str, object] | None = None


class AgentRunCreate(BaseModel):
    job_id: UUID | None = None
    agent_name: str
    input_json: dict[str, object]
    output_json: dict[str, object] | None = None
    status: str
    error_message: str | None = None
    token_usage: dict[str, object] = Field(default_factory=dict)
    duration_ms: int | None = None


class AgentRunResponse(AgentRunCreate):
    id: UUID
    user_id: UUID
    created_at: datetime | None
    finished_at: datetime | None

    model_config = {"from_attributes": True}
