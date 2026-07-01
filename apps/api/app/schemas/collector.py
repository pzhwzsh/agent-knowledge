from datetime import datetime

from pydantic import BaseModel, Field


class CollectedItem(BaseModel):
    url: str = Field(max_length=1000)
    title: str = Field(max_length=500)
    summary: str | None = None
    source_type: str
    source_name: str | None = Field(default=None, max_length=255)
    published_at: datetime | None = None
    topics: list[str] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)
