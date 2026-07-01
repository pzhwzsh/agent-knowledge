from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.enums import JobStatus
from app.models.job import IngestionJob
from app.schemas.ingestion import IngestionJobCreate
from app.services.ingestions import IngestionService
from app.tasks import jobs


def create_user_and_job(db: Session) -> tuple[UUID, UUID]:
    from app.core.security import hash_password
    from app.models.user import User

    user = User(email="task@example.com", password_hash=hash_password("password123"))
    db.add(user)
    db.commit()
    db.refresh(user)
    job = IngestionService(db).create_job(
        user.id,
        IngestionJobCreate(input_type="text", input_value="task processing content"),
    )
    return user.id, job.id


def test_process_ingestion_job_task_uses_existing_job(monkeypatch, db_session: Session) -> None:
    user_id, job_id = create_user_and_job(db_session)
    monkeypatch.setattr(jobs, "SessionLocal", lambda: db_session)

    result = jobs.process_ingestion_job(str(user_id), str(job_id))

    assert result["job"]["status"] == "success"
    assert result["content"]["source_type"] == "text"


def test_generate_user_recommendations_task_creates_ingestion(monkeypatch, db_session: Session) -> None:
    from app.core.security import hash_password
    from app.models.user import User

    user = User(email="task-generate@example.com", password_hash=hash_password("password123"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    monkeypatch.setattr(jobs, "SessionLocal", lambda: db_session)

    result = jobs.generate_user_recommendations(str(user.id), "text", "generate recommendation content")

    assert result["job"]["status"] == "success"
    assert result["content"] is not None


def test_cleanup_failed_jobs_marks_stale_running_jobs(monkeypatch, db_session: Session) -> None:
    user_id, job_id = create_user_and_job(db_session)
    job = db_session.get(IngestionJob, job_id)
    assert job is not None
    job.status = JobStatus.RUNNING.value
    job.updated_at = datetime.now(UTC) - timedelta(hours=2)
    db_session.add(job)
    db_session.commit()
    monkeypatch.setattr(jobs, "SessionLocal", lambda: db_session)

    result = jobs.cleanup_failed_jobs(older_than_minutes=60)
    updated = db_session.get(IngestionJob, job_id)

    assert result == {"marked_failed": 1}
    assert updated is not None
    assert updated.status == JobStatus.FAILED.value


def test_embed_document_chunks_task_updates_embeddings(monkeypatch, client, db_session: Session) -> None:
    def register_and_login(email: str) -> str:
        response = client.post("/api/auth/register", json={"email": email, "password": "password123"})
        assert response.status_code == 201
        response = client.post("/api/auth/login", json={"email": email, "password": "password123"})
        assert response.status_code == 200
        return response.json()["access_token"]

    token = register_and_login("task-embed@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    monkeypatch.setattr(jobs, "SessionLocal", lambda: db_session)
    content_response = client.post(
        "/api/ingestions",
        headers=headers,
        json={"input_type": "text", "input_value": "embedding task content " * 20},
    )
    queued = content_response.json()
    processed = jobs.process_ingestion_job(queued["job"]["user_id"], queued["job"]["id"])
    content_id = processed["content"]["id"]
    document_response = client.post(
        "/api/documents/from-content",
        headers=headers,
        json={"content_id": content_id, "category": "other"},
    )
    document = document_response.json()
    result = jobs.embed_document_chunks(document["user_id"], document["id"])

    assert result["updated"] >= 1


def test_fetch_daily_sources_for_active_users_queues_tasks(monkeypatch, db_session: Session) -> None:
    from app.core.security import hash_password
    from app.models.user import User

    user = User(email="task-active@example.com", password_hash=hash_password("password123"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    monkeypatch.setattr(jobs, "SessionLocal", lambda: db_session)

    queued = []

    class FakeAsyncResult:
        id = "fake-task-id"

    def fake_delay(user_id: str, *, github_limit: int):
        queued.append({"user_id": user_id, "github_limit": github_limit})
        return FakeAsyncResult()

    monkeypatch.setattr(jobs.fetch_daily_sources, "delay", fake_delay)

    result = jobs.fetch_daily_sources_for_active_users(github_limit=3)

    assert result["queued"] == 1
    assert queued == [{"user_id": str(user.id), "github_limit": 3}]


def test_celery_beat_schedule_contains_core_jobs() -> None:
    from app.tasks.celery_app import celery_app

    assert "cleanup-failed-jobs" in celery_app.conf.beat_schedule
    assert "fetch-daily-sources-for-active-users" in celery_app.conf.beat_schedule


def test_task_schedule_endpoint(client) -> None:
    response = client.get("/api/tasks/schedule")

    assert response.status_code == 200
    data = response.json()
    assert data["timezone"]
    assert any(item["task"] == "cleanup_failed_jobs" for item in data["beat_schedule"])
    assert "cleanup_failed_jobs" in data["registered_tasks"]
