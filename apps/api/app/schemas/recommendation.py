from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.document import DocumentWithChunksResponse


class RecommendationCreate(BaseModel):
    content_id: UUID
    score: float = Field(ge=0)
    category: str
    summary: str | None = None
    reason: str | None = None
    tags: list[str] = Field(default_factory=list)
    status: str = "pending"


class RecommendationGenerateRequest(BaseModel):
    content_id: UUID


class RecommendationStatusUpdate(BaseModel):
    status: str


class RecommendationResponse(RecommendationCreate):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RecommendationSaveResponse(BaseModel):
    recommendation: RecommendationResponse
    document: DocumentWithChunksResponse
