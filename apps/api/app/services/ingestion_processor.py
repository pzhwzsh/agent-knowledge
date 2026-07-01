from time import perf_counter
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agents.general import GeneralAgent
from app.agents.github import GitHubAgent
from app.agents.lifestyle import LifestyleAgent
from app.agents.router import RouterAgent
from app.models.content import Content
from app.models.enums import AgentRunStatus, JobStatus
from app.models.job import IngestionJob
from app.repositories.contents import ContentRepository
from app.schemas.ingestion import AgentRunCreate, IngestionJobCreate, IngestionSubmitResponse
from app.services.content_builder import ContentBuilder
from app.services.ingestions import IngestionService


class IngestionProcessor:
    def __init__(self, db: Session, content_builder: ContentBuilder | None = None) -> None:
        self.db = db
        self.content_builder = content_builder or ContentBuilder()
        self.ingestions = IngestionService(db)
        self.contents = ContentRepository(db)
        self.router_agent = RouterAgent()

    def submit(self, user_id: UUID, payload: IngestionJobCreate) -> IngestionSubmitResponse:
        job = self.ingestions.create_job(user_id, payload)
        return self.process_existing_job(user_id, job.id)

    def process_existing_job(self, user_id: UUID | str, job_id: UUID | str) -> IngestionSubmitResponse:
        user_uuid = UUID(str(user_id))
        job_uuid = UUID(str(job_id))
        job = self.ingestions.get_job(user_uuid, job_uuid)
        payload = IngestionJobCreate(input_type=job.input_type, input_value=job.input_value)
        return self._process_job(user_uuid, job, payload)

    def _process_job(
        self,
        user_id: UUID,
        job: IngestionJob,
        payload: IngestionJobCreate,
    ) -> IngestionSubmitResponse:
        try:
            self.ingestions.mark_job_status(user_id, job.id, JobStatus.RUNNING)
            content_payload = self.content_builder.build(payload)
            content = self.contents.get_or_create(content_payload)
            self.db.commit()
            self.db.refresh(content)

            route = self.router_agent.run(
                {
                    "source": content.canonical_url or content.url or "",
                    "text": content.raw_text or "",
                }
            )
            summary = self._run_summary_agent(route.route_to, content)
            self._record_agent_run(user_id, job.id, route, summary)
            job = self.ingestions.mark_job_status(user_id, job.id, JobStatus.SUCCESS)
            return IngestionSubmitResponse(
                job=job,
                content=content,
                route=route.model_dump(),
                summary=summary.model_dump(),
            )
        except HTTPException as exc:
            self.ingestions.mark_job_status(user_id, job.id, JobStatus.FAILED, error_message=str(exc.detail))
            raise
        except Exception as exc:
            self.ingestions.mark_job_status(user_id, job.id, JobStatus.FAILED, error_message=str(exc))
            raise

    def _run_summary_agent(self, route_to: str, content: Content) -> BaseModel:
        payload = {
            "title": content.title or "Untitled",
            "text": content.raw_text or "",
            "source": content.canonical_url or content.url or "",
        }
        if route_to == "github_agent":
            return GitHubAgent().run({"description": content.title or "", "readme": content.raw_text or ""})
        if route_to == "lifestyle_agent":
            return LifestyleAgent().run(payload)
        return GeneralAgent().run(payload)

    def _record_agent_run(self, user_id: UUID, job_id: UUID, route: BaseModel, summary: BaseModel) -> None:
        started = perf_counter()
        self.ingestions.record_agent_run(
            user_id,
            AgentRunCreate(
                job_id=job_id,
                agent_name="router_and_summary",
                input_json={"route": route.model_dump()},
                output_json={"summary": summary.model_dump()},
                status=AgentRunStatus.SUCCESS.value,
                duration_ms=int((perf_counter() - started) * 1000),
            ),
        )
