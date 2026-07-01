from math import sqrt
from uuid import UUID

from sqlalchemy.orm import Session

from app.llm.base import ChatModel, EmbeddingModel
from app.llm.providers import get_chat_model, get_embedding_model
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
    def __init__(
        self,
        db: Session,
        *,
        embedding_model: EmbeddingModel | None = None,
        chat_model: ChatModel | None = None,
    ) -> None:
        self.db = db
        self.chunks = DocumentChunkRepository(db)
        self.embedding_model = embedding_model or get_embedding_model()
        self.chat_model = chat_model or get_chat_model()

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
                answer="不知道。你的知识库里还没有足够的相关内容。",
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
        answer = self.chat_model.complete(
            [
                {
                    "role": "system",
                    "content": (
                        "你是个人知识库问答助手。只能基于用户提供的知识库片段回答；"
                        "如果片段不足以回答，明确说不知道。回答要简洁，并尽量标注引用编号，如 [1]。"
                    ),
                },
                {
                    "role": "user",
                    "content": self._build_rag_prompt(payload.question, search_response.results),
                },
            ]
        )
        return ChatResponse(
            answer=answer,
            citations=citations,
            related_documents=search_response.results,
        )


    def _build_rag_prompt(self, question: str, results: list[SearchResult]) -> str:
        context = "\n\n".join(
            f"[{index}] 标题：{result.title}\n内容：{result.content}"
            for index, result in enumerate(results, start=1)
        )
        return (
            f"问题：{question}\n\n"
            f"知识库片段：\n{context}\n\n"
            "请只基于这些片段回答，并在答案中保留必要引用编号。"
        )

    def _rank_chunks(
        self,
        user_id: UUID,
        query_embedding: list[float],
        *,
        limit: int,
    ) -> list[tuple[DocumentChunk, float]]:
        database_ranked = self.chunks.search_similar_for_user(user_id, query_embedding, limit=limit)
        if database_ranked is not None:
            return database_ranked

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
