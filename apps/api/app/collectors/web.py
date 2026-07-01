from datetime import UTC, datetime

import httpx
import trafilatura
from bs4 import BeautifulSoup
from fastapi import HTTPException, status

from app.collectors.base import Collector
from app.core.url_security import validate_public_http_url


class WebPageCollector(Collector):
    def __init__(self, *, timeout: float = 15.0, client: httpx.Client | None = None) -> None:
        self.timeout = timeout
        self.client = client

    def fetch(self, source: str) -> str:
        fetched = self.fetch_page(source)
        return fetched["text"]

    def fetch_page(self, source: str) -> dict[str, str]:
        validate_public_http_url(source)
        client = self.client or httpx.Client(timeout=self.timeout, follow_redirects=True)
        try:
            response = client.get(source)
            response.raise_for_status()
            final_url = validate_public_http_url(str(response.url))
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to fetch URL: HTTP {exc.response.status_code}",
            ) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to fetch URL") from exc

        html = response.text
        text = trafilatura.extract(html) or BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
        title = _extract_title(html) or source
        if not text.strip():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No readable text found")
        return {
            "url": final_url,
            "title": title,
            "text": text.strip(),
            "fetched_at": datetime.now(UTC).isoformat(),
        }


def _extract_title(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    return None
