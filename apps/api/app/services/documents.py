from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.document import Document
from app.repositories.documents import DocumentChunkRepository, DocumentRepository
from app.schemas.document import DocumentChunkCreate, DocumentCreate, DocumentUpdate, DocumentWithChunksResponse


class DocumentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.documents = DocumentRepository(db)
        self.chunks = DocumentChunkRepository(db)

    def list_documents(self, user_id: UUID, *, limit: int = 50, offset: int = 0) -> list[Document]:
        return self.documents.list_for_user(user_id, limit=limit, offset=offset)

    def get_document(self, user_id: UUID, document_id: UUID) -> Document:
        document = self.documents.get_for_user(user_id, document_id)
        if document is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        return document

    def get_document_with_chunks(self, user_id: UUID, document_id: UUID) -> DocumentWithChunksResponse:
        document = self.get_document(user_id, document_id)
        chunks = self.chunks.list_for_document(user_id, document.id)
        data = DocumentWithChunksResponse.model_validate(document).model_dump()
        data["chunks"] = chunks
        return DocumentWithChunksResponse.model_validate(data)

    def create_document_idempotent(self, user_id: UUID, payload: DocumentCreate) -> Document:
        if payload.content_id is not None:
            existing = self.documents.get_by_user_content(user_id, payload.content_id)
            if existing is not None:
                return existing
        document = self.documents.create_for_user(user_id, payload)
        self.db.commit()
        self.db.refresh(document)
        return document

    def update_document(self, user_id: UUID, document_id: UUID, payload: DocumentUpdate) -> Document:
        document = self.documents.update_for_user(user_id, document_id, payload)
        if document is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        self.db.commit()
        self.db.refresh(document)
        return document

    def delete_document(self, user_id: UUID, document_id: UUID) -> None:
        deleted = self.documents.delete_for_user(user_id, document_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        self.db.commit()

    def add_chunk(self, user_id: UUID, payload: DocumentChunkCreate):
        if self.documents.get_for_user(user_id, payload.document_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        chunk = self.chunks.create_for_user(user_id, payload)
        self.db.commit()
        self.db.refresh(chunk)
        return chunk
