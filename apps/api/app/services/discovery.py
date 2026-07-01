from datetime import UTC, datetime
from hashlib import sha256
from uuid import UUID

from sqlalchemy.orm import Session

from app.collectors.github import GitHubTrendingCollector
from app.collectors.rss import RSSCollector
from app.repositories.contents import ContentRepository
from app.schemas.collector import CollectedItem
from app.schemas.content import ContentCreate
from app.schemas.discovery import DiscoveryResponse
from app.services.recommendations import RecommendationService


class DiscoveryService:
    def __init__(
        self,
        db: Session,
        *,
        github_collector: GitHubTrendingCollector | None = None,
        rss_collector: RSSCollector | None = None,
    ) -> None:
        self.db = db
        self.contents = ContentRepository(db)
        self.recommendations = RecommendationService(db)
        self.github_collector = github_collector or GitHubTrendingCollector()
        self.rss_collector = rss_collector or RSSCollector()

    def discover_github_trending(
        self,
        user_id: UUID,
        *,
        language: str | None,
        limit: int,
    ) -> DiscoveryResponse:
        items = self.github_collector.fetch_trending(language=language, limit=limit)
        return self._store_and_recommend(user_id, items)

    def discover_rss(self, user_id: UUID, *, url: str, limit: int) -> DiscoveryResponse:
        items = self.rss_collector.fetch_feed(url, limit=limit)
        return self._store_and_recommend(user_id, items)

    def _store_and_recommend(self, user_id: UUID, items: list[CollectedItem]) -> DiscoveryResponse:
        content_ids = []
        recommendations = []
        for item in items:
            content = self.contents.get_or_create(_content_from_item(item))
            self.db.commit()
            self.db.refresh(content)
            content_ids.append(content.id)
            recommendations.append(self.recommendations.generate_for_content(user_id, content.id))
        return DiscoveryResponse(content_ids=content_ids, recommendations=recommendations)


def _content_from_item(item: CollectedItem) -> ContentCreate:
    raw_text = "\n".join(part for part in [item.title, item.summary] if part)
    return ContentCreate(
        url=item.url,
        canonical_url=item.url,
        title=item.title,
        source_type=item.source_type,
        source_name=item.source_name,
        raw_text=raw_text,
        content_hash=sha256(f"{item.url}|{raw_text}".encode("utf-8")).hexdigest(),
        published_at=item.published_at,
        fetched_at=datetime.now(UTC),
    )
