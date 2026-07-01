from uuid import UUID

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=20)


class Citation(BaseModel):
    document_id: UUID
    title: str
    source_url: str | None
    chunk_id: UUID


class SearchResult(BaseModel):
    chunk_id: UUID
    document_id: UUID
    title: str
    source_url: str | None
    content: str
    score: float


class SearchResponse(BaseModel):
    results: list[SearchResult]


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=20)


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    related_documents: list[SearchResult]
