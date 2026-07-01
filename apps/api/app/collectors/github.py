import httpx
from bs4 import BeautifulSoup
from fastapi import HTTPException, status

from app.models.enums import SourceType
from app.schemas.collector import CollectedItem

GITHUB_TRENDING_URL = "https://github.com/trending"


class GitHubTrendingCollector:
    def __init__(self, *, timeout: float = 15.0, client: httpx.Client | None = None) -> None:
        self.timeout = timeout
        self.client = client

    def fetch_trending(self, *, language: str | None = None, limit: int = 10) -> list[CollectedItem]:
        url = f"{GITHUB_TRENDING_URL}/{language}" if language else GITHUB_TRENDING_URL
        client = self.client or httpx.Client(timeout=self.timeout, follow_redirects=True)
        try:
            response = client.get(url)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to fetch GitHub Trending: HTTP {exc.response.status_code}",
            ) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to fetch GitHub Trending") from exc
        return _parse_trending_html(response.text, limit=limit)


def _parse_trending_html(html: str, *, limit: int) -> list[CollectedItem]:
    soup = BeautifulSoup(html, "html.parser")
    items: list[CollectedItem] = []
    for article in soup.select("article.Box-row")[:limit]:
        heading = article.select_one("h2 a")
        if heading is None:
            continue
        repo_path = " ".join(heading.get_text(" ", strip=True).split()).replace(" / ", "/")
        description_node = article.select_one("p")
        language_node = article.select_one('[itemprop="programmingLanguage"]')
        stars_node = article.select_one('a[href$="/stargazers"]')
        repo_url = f"https://github.com/{repo_path}"
        topics = [language_node.get_text(strip=True)] if language_node else []
        items.append(
            CollectedItem(
                url=repo_url,
                title=repo_path,
                summary=description_node.get_text(" ", strip=True) if description_node else None,
                source_type=SourceType.GITHUB.value,
                source_name="GitHub Trending",
                topics=topics,
                metadata={"stars_text": stars_node.get_text(" ", strip=True) if stars_node else None},
            )
        )
    return items
