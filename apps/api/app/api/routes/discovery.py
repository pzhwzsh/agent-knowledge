from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.discovery import DiscoveryResponse, GitHubTrendingRequest, RSSDiscoveryRequest
from app.services.discovery import DiscoveryService

router = APIRouter()


@router.post("/github-trending", response_model=DiscoveryResponse)
def discover_github_trending(
    payload: GitHubTrendingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return DiscoveryService(db).discover_github_trending(
        current_user.id,
        language=payload.language,
        limit=payload.limit,
    )


@router.post("/rss", response_model=DiscoveryResponse)
def discover_rss(
    payload: RSSDiscoveryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return DiscoveryService(db).discover_rss(current_user.id, url=payload.url, limit=payload.limit)
