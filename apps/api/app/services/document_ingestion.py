from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.llm.providers import get_embedding_model
from app.repositories.contents import ContentRepository
from app.repositories.documents import DocumentChunkRepository, DocumentRepository
from app.schemas.document import DocumentChunkCreate, DocumentCreate, DocumentCreateFromContent
from app.services.chunking import TextChunker
from app.services.documents import DocumentService


class DocumentIngestionService:
    def __init__(
        self,
        db: Session,
        *,
        chunker: TextChunker | None = None,
    ) -> None:
        self.db = db
        self.contents = ContentRepository(db)
        self.documents = DocumentRepository(db)
        self.chunks = DocumentChunkRepository(db)
        self.document_service = DocumentService(db)
        self.chunker = chunker or TextChunker()

    def create_from_content(self, user_id: UUID, payload: DocumentCreateFromContent):
        content = self.contents.get_by_id(payload.content_id)
        if content is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")

        existing = self.documents.get_by_user_content(user_id, content.id)
        if existing is not None:
            return self.document_service.get_document_with_chunks(user_id, existing.id)

        document = self.documents.create_for_user(
            user_id,
            DocumentCreate(
                content_id=content.id,
                title=content.title or "Untitled",
                source_url=content.canonical_url or content.url,
                source_type=content.source_type,
                category=payload.category,
                summary=payload.summary,
                long_summary=payload.long_summary,
                tags=payload.tags,
            ),
        )
        self.db.flush()

        embedding_model = get_embedding_model()
        text = content.raw_text or content.title or ""
        chunks = self.chunker.split(
            text,
            metadata={
                "document_id": str(document.id),
                "user_id": str(user_id),
                "title": document.title,
                "source_url": document.source_url,
                "category": document.category,
                "tags": document.tags,
            },
        )
        for chunk in chunks:
            self.chunks.create_for_user(
                user_id,
                DocumentChunkCreate(
                    document_id=document.id,
                    chunk_index=chunk.index,
                    content=chunk.content,
                    embedding=embedding_model.embed(chunk.content),
                    metadata_json=chunk.metadata,
                ),
            )
        self.db.commit()
        return self.document_service.get_document_with_chunks(user_id, document.id)
