from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job import AgentRun, IngestionJob
from app.schemas.ingestion import AgentRunCreate, IngestionJobCreate


class IngestionJobRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_user(self, user_id: UUID, *, limit: int = 50, offset: int = 0) -> list[IngestionJob]:
        statement = (
            select(IngestionJob)
            .where(IngestionJob.user_id == user_id)
            .order_by(IngestionJob.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.scalars(statement))

    def get_for_user(self, user_id: UUID, job_id: UUID) -> IngestionJob | None:
        return self.db.scalar(select(IngestionJob).where(IngestionJob.user_id == user_id, IngestionJob.id == job_id))

    def list_by_status(self, status: str, *, limit: int = 100) -> list[IngestionJob]:
        statement = (
            select(IngestionJob)
            .where(IngestionJob.status == status)
            .order_by(IngestionJob.created_at.asc())
            .limit(limit)
        )
        return list(self.db.scalars(statement))

    def list_stale_active(self, *, older_than: timedelta, limit: int = 100) -> list[IngestionJob]:
        cutoff = datetime.now(UTC) - older_than
        statement = (
            select(IngestionJob)
            .where(IngestionJob.status.in_(["running", "retrying"]), IngestionJob.updated_at < cutoff)
            .order_by(IngestionJob.updated_at.asc())
            .limit(limit)
        )
        return list(self.db.scalars(statement))

    def create_for_user(self, user_id: UUID, payload: IngestionJobCreate) -> IngestionJob:
        job = IngestionJob(user_id=user_id, **payload.model_dump())
        self.db.add(job)
        self.db.flush()
        return job

    def mark_status(
        self,
        user_id: UUID,
        job_id: UUID,
        status: str,
        *,
        error_message: str | None = None,
        finished: bool = False,
    ) -> IngestionJob | None:
        job = self.get_for_user(user_id, job_id)
        if job is None:
            return None
        job.status = status
        job.error_message = error_message
        if finished:
            job.finished_at = datetime.now(UTC)
        self.db.add(job)
        self.db.flush()
        return job


class AgentRunRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_for_user(self, user_id: UUID, payload: AgentRunCreate) -> AgentRun:
        run = AgentRun(user_id=user_id, created_at=datetime.now(UTC), **payload.model_dump())
        self.db.add(run)
        self.db.flush()
        return run

    def list_for_user(self, user_id: UUID, *, limit: int = 50, offset: int = 0) -> list[AgentRun]:
        statement = (
            select(AgentRun)
            .where(AgentRun.user_id == user_id)
            .order_by(AgentRun.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.scalars(statement))
