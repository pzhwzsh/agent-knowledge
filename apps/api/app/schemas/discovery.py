from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.recommendation import RecommendationResponse


class GitHubTrendingRequest(BaseModel):
    language: str | None = None
    limit: int = Field(default=10, ge=1, le=50)


class RSSDiscoveryRequest(BaseModel):
    url: str
    limit: int = Field(default=20, ge=1, le=50)


class DiscoveryResponse(BaseModel):
    content_ids: list[UUID]
    recommendations: list[RecommendationResponse]
