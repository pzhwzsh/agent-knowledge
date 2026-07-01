from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import JobStatus
from app.models.job import IngestionJob
from app.repositories.ingestions import AgentRunRepository, IngestionJobRepository
from app.schemas.ingestion import AgentRunCreate, IngestionJobCreate


class IngestionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.jobs = IngestionJobRepository(db)
        self.agent_runs = AgentRunRepository(db)

    def list_jobs(self, user_id: UUID, *, limit: int = 50, offset: int = 0) -> list[IngestionJob]:
        return self.jobs.list_for_user(user_id, limit=limit, offset=offset)

    def get_job(self, user_id: UUID, job_id: UUID) -> IngestionJob:
        job = self.jobs.get_for_user(user_id, job_id)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingestion job not found")
        return job

    def create_job(self, user_id: UUID, payload: IngestionJobCreate) -> IngestionJob:
        job = self.jobs.create_for_user(user_id, payload)
        self.db.commit()
        self.db.refresh(job)
        return job

    def reset_failed_job_for_retry(self, user_id: UUID, job_id: UUID) -> IngestionJob:
        job = self.get_job(user_id, job_id)
        if job.status != JobStatus.FAILED.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only failed ingestion jobs can be replayed",
            )
        reset_job = self.jobs.reset_for_retry(user_id, job_id)
        if reset_job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingestion job not found")
        self.db.commit()
        self.db.refresh(reset_job)
        return reset_job

    def mark_job_status(
        self,
        user_id: UUID,
        job_id: UUID,
        job_status: JobStatus,
        *,
        error_message: str | None = None,
    ) -> IngestionJob:
        job = self.jobs.mark_status(
            user_id,
            job_id,
            job_status.value,
            error_message=error_message,
            finished=job_status in {JobStatus.SUCCESS, JobStatus.FAILED},
        )
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingestion job not found")
        self.db.commit()
        self.db.refresh(job)
        return job

    def record_agent_run(self, user_id: UUID, payload: AgentRunCreate):
        run = self.agent_runs.create_for_user(user_id, payload)
        self.db.commit()
        self.db.refresh(run)
        return run
