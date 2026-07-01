from math import sqrt
from uuid import UUID

from sqlalchemy.orm import Session

from app.llm.providers import get_embedding_model
from app.models.document import DocumentChunk
from app.repositories.documents import DocumentChunkRepository
from app.schemas.search import (
    ChatRequest,
    ChatResponse,
    Citation,
    SearchRequest,
    SearchResponse,
    SearchResult,
)


class SearchService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.chunks = DocumentChunkRepository(db)
        self.embedding_model = get_embedding_model()

    def search(self, user_id: UUID, payload: SearchRequest) -> SearchResponse:
        query_embedding = self.embedding_model.embed(payload.query)
        ranked = self._rank_chunks(user_id, query_embedding, limit=payload.limit)
        return SearchResponse(results=[self._to_result(chunk, score) for chunk, score in ranked])

    def chat(self, user_id: UUID, payload: ChatRequest) -> ChatResponse:
        search_response = self.search(
            user_id,
            SearchRequest(query=payload.question, limit=payload.limit),
        )
        if not search_response.results:
            return ChatResponse(
                answer="????????????????????????",
                citations=[],
                related_documents=[],
            )

        citations = [
            Citation(
                document_id=result.document_id,
                title=result.title,
                source_url=result.source_url,
                chunk_id=result.chunk_id,
            )
            for result in search_response.results
        ]
        facts = "\n".join(f"- {result.content}" for result in search_response.results[:3])
        answer = (
            "???\n"
            f"{facts}\n\n"
            "?????????????????????????????????\n\n"
            "???????????????????????????????????????"
        )
        return ChatResponse(
            answer=answer,
            citations=citations,
            related_documents=search_response.results,
        )

    def _rank_chunks(
        self,
        user_id: UUID,
        query_embedding: list[float],
        *,
        limit: int,
    ) -> list[tuple[DocumentChunk, float]]:
        ranked: list[tuple[DocumentChunk, float]] = []
        for chunk in self.chunks.list_searchable_for_user(user_id):
            if chunk.embedding is None:
                continue
            score = _cosine_similarity(query_embedding, chunk.embedding)
            ranked.append((chunk, score))
        ranked.sort(key=lambda item: item[1], reverse=True)
        return ranked[:limit]

    def _to_result(self, chunk: DocumentChunk, score: float) -> SearchResult:
        document = chunk.document
        return SearchResult(
            chunk_id=chunk.id,
            document_id=document.id,
            title=document.title,
            source_url=document.source_url,
            content=chunk.content,
            score=score,
        )


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    length = min(len(left), len(right))
    if length == 0:
        return 0.0
    left_slice = left[:length]
    right_slice = right[:length]
    dot = sum(a * b for a, b in zip(left_slice, right_slice, strict=True))
    left_norm = sqrt(sum(value * value for value in left_slice))
    right_norm = sqrt(sum(value * value for value in right_slice))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)
