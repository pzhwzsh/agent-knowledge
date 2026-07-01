from uuid import UUID

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.content import Content
from app.models.job import AgentRun, IngestionJob
from app.services.ingestion_processor import IngestionProcessor


def register_and_login(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 201, response.text
    response = client.post("/api/auth/login", json={"email": email, "password": "password123"})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def process_job(db_session: Session, queued: dict) -> dict:
    job = queued["job"]
    return IngestionProcessor(db_session).process_existing_job(job["user_id"], job["id"]).model_dump(mode="json")


def test_submit_text_ingestion_queues_pending_job(
    client: TestClient,
    db_session: Session,
) -> None:
    token = register_and_login(client, "ingest@example.com")

    response = client.post(
        "/api/ingestions",
        headers=auth_header(token),
        json={"input_type": "text", "input_value": "daily cooking running lifestyle"},
    )

    assert response.status_code == 202, response.text
    body = response.json()
    assert body["job"]["status"] == "pending"
    assert body["task_id"] == "test-task-id"
    assert db_session.scalar(select(IngestionJob).where(IngestionJob.status == "pending")) is not None
    assert db_session.scalar(select(AgentRun)) is None


def test_process_existing_text_ingestion_creates_success_job_content_and_agent_run(
    client: TestClient,
    db_session: Session,
) -> None:
    token = register_and_login(client, "ingest-process@example.com")
    queued = client.post(
        "/api/ingestions",
        headers=auth_header(token),
        json={"input_type": "text", "input_value": "daily cooking running lifestyle"},
    ).json()

    body = process_job(db_session, queued)

    assert body["job"]["status"] == "success"
    assert body["content"]["source_type"] == "text"
    assert body["route"]["route_to"] in {"general_agent", "lifestyle_agent", "github_agent"}
    assert db_session.scalar(select(IngestionJob).where(IngestionJob.status == "success")) is not None
    assert db_session.scalar(select(AgentRun)) is not None


def test_duplicate_text_ingestion_reuses_content(client: TestClient, db_session: Session) -> None:
    token = register_and_login(client, "dedupe@example.com")
    payload = {"input_type": "text", "input_value": "duplicate content"}

    first = client.post("/api/ingestions", headers=auth_header(token), json=payload)
    second = client.post("/api/ingestions", headers=auth_header(token), json=payload)

    assert first.status_code == 202, first.text
    assert second.status_code == 202, second.text
    first_processed = process_job(db_session, first.json())
    second_processed = process_job(db_session, second.json())
    assert first_processed["content"]["id"] == second_processed["content"]["id"]
    assert len(list(db_session.scalars(select(Content)))) == 1


def test_ingestion_jobs_are_listed_only_for_current_user(client: TestClient) -> None:
    alice = register_and_login(client, "alice-ingest@example.com")
    bob = register_and_login(client, "bob-ingest@example.com")

    client.post(
        "/api/ingestions",
        headers=auth_header(alice),
        json={"input_type": "text", "input_value": "alice content"},
    )
    client.post(
        "/api/ingestions",
        headers=auth_header(bob),
        json={"input_type": "text", "input_value": "bob content"},
    )

    alice_jobs = client.get("/api/ingestions", headers=auth_header(alice))
    bob_jobs = client.get("/api/ingestions", headers=auth_header(bob))

    assert alice_jobs.status_code == 200
    assert bob_jobs.status_code == 200
    assert len(alice_jobs.json()) == 1
    assert len(bob_jobs.json()) == 1
    assert alice_jobs.json()[0]["input_value"] == "alice content"
    assert bob_jobs.json()[0]["input_value"] == "bob content"


def test_private_url_fails_when_worker_processes_job(client: TestClient, db_session: Session) -> None:
    token = register_and_login(client, "ssrf@example.com")

    response = client.post(
        "/api/ingestions",
        headers=auth_header(token),
        json={"input_type": "url", "input_value": "http://127.0.0.1/admin"},
    )

    assert response.status_code == 202
    with pytest.raises(HTTPException) as exc_info:
        process_job(db_session, response.json())
    assert "Private or reserved" in str(exc_info.value.detail) or "Localhost" in str(exc_info.value.detail)
    job = db_session.get(IngestionJob, UUID(response.json()["job"]["id"]))
    assert job is not None
    assert job.status == "failed"
    assert job.error_message
