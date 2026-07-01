from datetime import datetime
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

import httpx
from fastapi import HTTPException, status

from app.core.url_security import validate_public_http_url
from app.models.enums import SourceType
from app.schemas.collector import CollectedItem


class RSSCollector:
    def __init__(self, *, timeout: float = 15.0, client: httpx.Client | None = None) -> None:
        self.timeout = timeout
        self.client = client

    def fetch_feed(self, url: str, *, limit: int = 20) -> list[CollectedItem]:
        validate_public_http_url(url)
        client = self.client or httpx.Client(timeout=self.timeout, follow_redirects=True)
        try:
            response = client.get(url)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to fetch RSS feed: HTTP {exc.response.status_code}",
            ) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to fetch RSS feed") from exc
        return parse_feed(response.text, source_name=url, limit=limit)


def parse_feed(xml_text: str, *, source_name: str, limit: int = 20) -> list[CollectedItem]:
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid RSS feed") from exc
    if root.tag.endswith("feed"):
        return _parse_atom(root, source_name=source_name, limit=limit)
    return _parse_rss(root, source_name=source_name, limit=limit)


def _parse_rss(root: ElementTree.Element, *, source_name: str, limit: int) -> list[CollectedItem]:
    items: list[CollectedItem] = []
    for item in root.findall(".//item")[:limit]:
        title = _text(item, "title") or "Untitled"
        link = _text(item, "link")
        if not link:
            continue
        items.append(
            CollectedItem(
                url=link,
                title=title,
                summary=_text(item, "description"),
                source_type=SourceType.RSS.value,
                source_name=source_name,
                published_at=_parse_date(_text(item, "pubDate")),
            )
        )
    return items


def _parse_atom(root: ElementTree.Element, *, source_name: str, limit: int) -> list[CollectedItem]:
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entries = root.findall("atom:entry", ns) or root.findall("entry")
    items: list[CollectedItem] = []
    for entry in entries[:limit]:
        title = _text(entry, "{http://www.w3.org/2005/Atom}title") or _text(entry, "title") or "Untitled"
        link_node = entry.find("atom:link", ns) or entry.find("link")
        link = link_node.attrib.get("href") if link_node is not None else None
        if not link:
            continue
        items.append(
            CollectedItem(
                url=link,
                title=title,
                summary=_text(entry, "{http://www.w3.org/2005/Atom}summary") or _text(entry, "summary"),
                source_type=SourceType.RSS.value,
                source_name=source_name,
                published_at=_parse_date(_text(entry, "{http://www.w3.org/2005/Atom}updated") or _text(entry, "updated")),
            )
        )
    return items


def _text(node: ElementTree.Element, tag: str) -> str | None:
    child = node.find(tag)
    if child is None or child.text is None:
        return None
    return child.text.strip()


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return parsedate_to_datetime(value)
    except (TypeError, ValueError):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
