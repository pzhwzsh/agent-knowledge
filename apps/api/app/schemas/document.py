from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentCreate(BaseModel):
    content_id: UUID | None = None
    title: str = Field(max_length=500)
    source_url: str | None = Field(default=None, max_length=1000)
    source_type: str
    category: str
    summary: str | None = None
    long_summary: str | None = None
    tags: list[str] = Field(default_factory=list)


class DocumentCreateFromContent(BaseModel):
    content_id: UUID
    category: str = "other"
    summary: str | None = None
    long_summary: str | None = None
    tags: list[str] = Field(default_factory=list)


class DocumentUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=500)
    category: str | None = None
    summary: str | None = None
    long_summary: str | None = None
    tags: list[str] | None = None


class DocumentResponse(DocumentCreate):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentChunkCreate(BaseModel):
    document_id: UUID
    chunk_index: int = Field(ge=0)
    content: str
    embedding: list[float] | None = None
    metadata_json: dict[str, object] = Field(default_factory=dict)


class DocumentChunkResponse(DocumentChunkCreate):
    id: UUID
    user_id: UUID

    model_config = {"from_attributes": True}


class DocumentWithChunksResponse(DocumentResponse):
    chunks: list[DocumentChunkResponse] = Field(default_factory=list)
