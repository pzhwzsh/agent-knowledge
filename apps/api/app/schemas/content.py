from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SourceResponse(BaseModel):
    id: UUID
    name: str
    url: str | None
    source_type: str
    metadata_json: dict[str, object] | None

    model_config = {"from_attributes": True}


class ContentCreate(BaseModel):
    url: str | None = Field(default=None, max_length=1000)
    canonical_url: str | None = Field(default=None, max_length=1000)
    title: str | None = Field(default=None, max_length=500)
    author: str | None = Field(default=None, max_length=255)
    source_type: str
    source_name: str | None = Field(default=None, max_length=255)
    raw_text: str | None = None
    content_hash: str | None = Field(default=None, max_length=128)
    published_at: datetime | None = None
    fetched_at: datetime | None = None


class ContentResponse(ContentCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
