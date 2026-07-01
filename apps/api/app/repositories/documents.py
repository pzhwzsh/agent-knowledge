from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.document import Document, DocumentChunk
from app.schemas.document import DocumentChunkCreate, DocumentCreate, DocumentUpdate


class DocumentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_user(self, user_id: UUID, *, limit: int = 50, offset: int = 0) -> list[Document]:
        statement = (
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.scalars(statement))

    def get_for_user(self, user_id: UUID, document_id: UUID) -> Document | None:
        return self.db.scalar(select(Document).where(Document.user_id == user_id, Document.id == document_id))

    def get_by_user_content(self, user_id: UUID, content_id: UUID) -> Document | None:
        return self.db.scalar(
            select(Document).where(Document.user_id == user_id, Document.content_id == content_id)
        )

    def create_for_user(self, user_id: UUID, payload: DocumentCreate) -> Document:
        document = Document(user_id=user_id, **payload.model_dump())
        self.db.add(document)
        self.db.flush()
        return document

    def update_for_user(self, user_id: UUID, document_id: UUID, payload: DocumentUpdate) -> Document | None:
        document = self.get_for_user(user_id, document_id)
        if document is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(document, field, value)
        self.db.add(document)
        self.db.flush()
        return document

    def delete_for_user(self, user_id: UUID, document_id: UUID) -> bool:
        document = self.get_for_user(user_id, document_id)
        if document is None:
            return False
        self.db.delete(document)
        self.db.flush()
        return True


class DocumentChunkRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_document(self, user_id: UUID, document_id: UUID) -> list[DocumentChunk]:
        statement = (
            select(DocumentChunk)
            .where(DocumentChunk.user_id == user_id, DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index.asc())
        )
        return list(self.db.scalars(statement))

    def create_for_user(self, user_id: UUID, payload: DocumentChunkCreate) -> DocumentChunk:
        chunk = DocumentChunk(user_id=user_id, **payload.model_dump())
        self.db.add(chunk)
        self.db.flush()
        return chunk


    def list_searchable_for_user(self, user_id: UUID) -> list[DocumentChunk]:
        statement = (
            select(DocumentChunk)
            .options(joinedload(DocumentChunk.document))
            .where(DocumentChunk.user_id == user_id, DocumentChunk.embedding.is_not(None))
        )
        return list(self.db.scalars(statement))
