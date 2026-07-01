from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.enums import JobStatus
from app.models.user import User
from app.schemas.ingestion import IngestionJobCreate, IngestionJobResponse, IngestionQueueResponse
from app.services.ingestions import IngestionService
from app.tasks.jobs import process_ingestion_job

router = APIRouter()


@router.post("", response_model=IngestionQueueResponse, status_code=status.HTTP_202_ACCEPTED)
def submit_ingestion(
    payload: IngestionJobCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = IngestionService(db)
    job = service.create_job(current_user.id, payload)
    try:
        async_result = process_ingestion_job.delay(str(current_user.id), str(job.id))
    except Exception as exc:
        job = service.mark_job_status(
            current_user.id,
            job.id,
            JobStatus.FAILED,
            error_message=f"Failed to enqueue ingestion job: {exc}",
        )
        return IngestionQueueResponse(job=job, task_id=None)
    return IngestionQueueResponse(job=job, task_id=async_result.id)


@router.get("", response_model=list[IngestionJobResponse])
def list_ingestions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    return IngestionService(db).list_jobs(current_user.id, limit=limit, offset=offset)


@router.get("/{job_id}", response_model=IngestionJobResponse)
def get_ingestion(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return IngestionService(db).get_job(current_user.id, job_id)

@router.post("/{job_id}/replay", response_model=IngestionQueueResponse, status_code=status.HTTP_202_ACCEPTED)
def replay_ingestion(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = IngestionService(db)
    job = service.reset_failed_job_for_retry(current_user.id, job_id)
    try:
        async_result = process_ingestion_job.delay(str(current_user.id), str(job.id))
    except Exception as exc:
        job = service.mark_job_status(
            current_user.id,
            job.id,
            JobStatus.FAILED,
            error_message=f"Failed to enqueue ingestion replay: {exc}",
        )
        return IngestionQueueResponse(job=job, task_id=None)
    return IngestionQueueResponse(job=job, task_id=async_result.id)

