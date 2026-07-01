from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.document import (
    DocumentCreateFromContent,
    DocumentResponse,
    DocumentWithChunksResponse,
)
from app.services.document_ingestion import DocumentIngestionService
from app.services.documents import DocumentService

router = APIRouter()


@router.get("", response_model=list[DocumentResponse])
def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    return DocumentService(db).list_documents(current_user.id, limit=limit, offset=offset)


@router.post("/from-content", response_model=DocumentWithChunksResponse, status_code=status.HTTP_201_CREATED)
def create_document_from_content(
    payload: DocumentCreateFromContent,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return DocumentIngestionService(db).create_from_content(current_user.id, payload)


@router.get("/{document_id}", response_model=DocumentWithChunksResponse)
def get_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return DocumentService(db).get_document_with_chunks(current_user.id, document_id)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    DocumentService(db).delete_document(current_user.id, document_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
