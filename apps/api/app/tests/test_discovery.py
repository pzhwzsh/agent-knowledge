from uuid import UUID

import httpx
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.collectors.github import GitHubTrendingCollector
from app.collectors.rss import parse_feed
from app.models.document import Document
from app.models.recommendation import Recommendation
from app.services.discovery import DiscoveryService


def register_and_login(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 201, response.text
    response = client.post("/api/auth/login", json={"email": email, "password": "password123"})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_parse_github_trending_html() -> None:
    html = '\n    <article class="Box-row">\n      <h2><a href="/owner/repo"> owner / repo </a></h2>\n      <p>A useful FastAPI project</p>\n      <span itemprop="programmingLanguage">Python</span>\n      <a href="/owner/repo/stargazers">1,234</a>\n    </article>\n    '
    collector = GitHubTrendingCollector(
        client=httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, text=html)))
    )

    items = collector.fetch_trending(limit=1)

    assert len(items) == 1
    assert items[0].url == "https://github.com/owner/repo"
    assert items[0].title == "owner/repo"
    assert items[0].topics == ["Python"]


def test_parse_rss_feed() -> None:
    xml = '\n    <rss><channel><item>\n      <title>Example RSS</title>\n      <link>https://example.com/post</link>\n      <description>FastAPI article</description>\n      <pubDate>Mon, 29 Jun 2026 09:00:00 GMT</pubDate>\n    </item></channel></rss>\n    '

    items = parse_feed(xml, source_name="feed", limit=10)

    assert len(items) == 1
    assert items[0].title == "Example RSS"
    assert items[0].url == "https://example.com/post"


def test_discovery_service_generates_recommendations_without_documents(
    client: TestClient,
    db_session: Session,
) -> None:
    token = register_and_login(client, "discover@example.com")
    me = client.get("/api/auth/me", headers=auth_header(token)).json()
    html = '\n    <article class="Box-row">\n      <h2><a href="/owner/repo"> owner / repo </a></h2>\n      <p>fastapi agent knowledge base</p>\n      <span itemprop="programmingLanguage">Python</span>\n    </article>\n    '
    github = GitHubTrendingCollector(
        client=httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, text=html)))
    )

    response = DiscoveryService(db_session, github_collector=github).discover_github_trending(
        user_id=UUID(me["id"]),
        language=None,
        limit=1,
    )

    assert len(response.content_ids) == 1
    assert len(response.recommendations) == 1
    assert response.recommendations[0].status == "pending"
    assert db_session.scalar(select(Recommendation)) is not None
    assert list(db_session.scalars(select(Document))) == []


def test_discovery_api_requires_authentication(client: TestClient) -> None:
    response = client.post("/api/discovery/github-trending", json={"limit": 1})

    assert response.status_code == 401
