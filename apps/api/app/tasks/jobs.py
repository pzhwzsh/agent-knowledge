from datetime import timedelta
from uuid import UUID

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.llm.providers import get_embedding_model
from app.models.enums import JobStatus
from app.repositories.documents import DocumentChunkRepository, DocumentRepository
from app.repositories.ingestions import IngestionJobRepository
from app.repositories.users import UserRepository
from app.schemas.ingestion import IngestionJobCreate
from app.services.discovery import DiscoveryService
from app.services.ingestion_processor import IngestionProcessor
from app.services.ingestions import IngestionService
from app.services.push import RecommendationPushService
from app.tasks.celery_app import celery_app

settings = get_settings()
TASK_RETRY_KWARGS = {
    "autoretry_for": (Exception,),
    "retry_backoff": True,
    "retry_jitter": True,
    "max_retries": settings.celery_max_retries,
    "default_retry_delay": settings.celery_default_retry_delay_seconds,
}


@celery_app.task(name="process_ingestion_job", **TASK_RETRY_KWARGS)
def process_ingestion_job(user_id: str, job_id: str) -> dict[str, object]:
    with SessionLocal() as db:
        response = IngestionProcessor(db).process_existing_job(UUID(user_id), UUID(job_id))
        return response.model_dump(mode="json")


@celery_app.task(name="fetch_daily_sources", **TASK_RETRY_KWARGS)
def fetch_daily_sources(user_id: str, *, github_limit: int = 10) -> dict[str, object]:
    with SessionLocal() as db:
        user = UserRepository(db).get_active(UUID(user_id))
        if user is None:
            return {"skipped": True, "reason": "user_not_found_or_inactive"}
        response = DiscoveryService(db).discover_github_trending(
            user.id,
            language=None,
            limit=github_limit,
        )
        return response.model_dump(mode="json")


@celery_app.task(name="fetch_daily_sources_for_active_users")
def fetch_daily_sources_for_active_users(*, github_limit: int = 10, limit: int = 100) -> dict[str, object]:
    with SessionLocal() as db:
        users = UserRepository(db).list_active(limit=limit)
        queued = []
        for user in users:
            async_result = fetch_daily_sources.delay(str(user.id), github_limit=github_limit)
            queued.append({"user_id": str(user.id), "task_id": async_result.id})
        return {"queued": len(queued), "tasks": queued}


@celery_app.task(name="generate_user_recommendations", **TASK_RETRY_KWARGS)
def generate_user_recommendations(user_id: str, input_type: str, input_value: str) -> dict[str, object]:
    with SessionLocal() as db:
        response = IngestionProcessor(db).submit(
            UUID(user_id),
            IngestionJobCreate(input_type=input_type, input_value=input_value),
        )
        return response.model_dump(mode="json")


@celery_app.task(name="embed_document_chunks", **TASK_RETRY_KWARGS)
def embed_document_chunks(user_id: str, document_id: str) -> dict[str, object]:
    user_uuid = UUID(user_id)
    document_uuid = UUID(document_id)
    with SessionLocal() as db:
        document = DocumentRepository(db).get_for_user(user_uuid, document_uuid)
        if document is None:
            return {"updated": 0, "reason": "document_not_found"}
        chunks = DocumentChunkRepository(db).list_for_document(user_uuid, document_uuid)
        embedding_model = get_embedding_model()
        for chunk in chunks:
            chunk.embedding = embedding_model.embed(chunk.content)
            db.add(chunk)
        db.commit()
        return {"updated": len(chunks)}


@celery_app.task(name="cleanup_failed_jobs")
def cleanup_failed_jobs(*, older_than_minutes: int = 60, limit: int = 100) -> dict[str, object]:
    with SessionLocal() as db:
        repository = IngestionJobRepository(db)
        service = IngestionService(db)
        stale_jobs = repository.list_stale_active(older_than=timedelta(minutes=older_than_minutes), limit=limit)
        for job in stale_jobs:
            service.mark_job_status(
                job.user_id,
                job.id,
                JobStatus.FAILED,
                error_message="Marked failed by cleanup_failed_jobs after timeout.",
            )
        return {"marked_failed": len(stale_jobs)}


@celery_app.task(name="push_daily_recommendations", **TASK_RETRY_KWARGS)
def push_daily_recommendations(user_id: str) -> dict[str, object]:
    with SessionLocal() as db:
        user = UserRepository(db).get_active(UUID(user_id))
        if user is None:
            return {"skipped": True, "reason": "user_not_found_or_inactive"}
        return RecommendationPushService(db).push_daily_recommendations(user.id)


@celery_app.task(name="push_daily_recommendations_for_active_users")
def push_daily_recommendations_for_active_users(*, limit: int = 100) -> dict[str, object]:
    with SessionLocal() as db:
        users = UserRepository(db).list_active(limit=limit)
        queued = []
        for user in users:
            async_result = push_daily_recommendations.delay(str(user.id))
            queued.append({"user_id": str(user.id), "task_id": async_result.id})
        return {"queued": len(queued), "tasks": queued}
