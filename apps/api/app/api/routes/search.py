from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.search import ChatRequest, ChatResponse, SearchRequest, SearchResponse
from app.services.search import SearchService

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
def search_knowledge_base(
    payload: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return SearchService(db).search(current_user.id, payload)


@router.post("/chat", response_model=ChatResponse)
def chat_with_knowledge_base(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return SearchService(db).chat(current_user.id, payload)
