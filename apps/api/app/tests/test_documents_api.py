from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentChunk
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


def create_content(client: TestClient, token: str, db_session: Session, text: str = "knowledge base content " * 200) -> str:
    response = client.post(
        "/api/ingestions",
        headers=auth_header(token),
        json={"input_type": "text", "input_value": text},
    )
    assert response.status_code == 202, response.text
    queued = response.json()
    processed = IngestionProcessor(db_session).process_existing_job(queued["job"]["user_id"], queued["job"]["id"])
    return str(processed.content.id)


def test_create_document_from_content_builds_chunks_and_embeddings(
    client: TestClient,
    db_session: Session,
) -> None:
    token = register_and_login(client, "doc-create@example.com")
    content_id = create_content(client, token, db_session)

    response = client.post(
        "/api/documents/from-content",
        headers=auth_header(token),
        json={"content_id": content_id, "category": "learning", "tags": ["kb"]},
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["category"] == "learning"
    assert body["tags"] == ["kb"]
    assert len(body["chunks"]) >= 1
    assert body["chunks"][0]["embedding"] is not None
    assert db_session.scalar(select(Document)) is not None
    assert db_session.scalar(select(DocumentChunk)) is not None


def test_repeated_create_from_same_content_is_idempotent(client: TestClient, db_session: Session) -> None:
    token = register_and_login(client, "doc-idempotent@example.com")
    content_id = create_content(client, token, db_session)
    payload = {"content_id": content_id, "category": "other"}

    first = client.post("/api/documents/from-content", headers=auth_header(token), json=payload)
    second = client.post("/api/documents/from-content", headers=auth_header(token), json=payload)

    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert first.json()["id"] == second.json()["id"]
    assert len(list(db_session.scalars(select(Document)))) == 1
    chunk_count = len(list(db_session.scalars(select(DocumentChunk))))
    assert chunk_count == len(first.json()["chunks"])


def test_documents_are_isolated_by_current_user(client: TestClient, db_session: Session) -> None:
    alice = register_and_login(client, "alice-doc-api@example.com")
    bob = register_and_login(client, "bob-doc-api@example.com")
    alice_content = create_content(client, alice, db_session, "alice private content")
    bob_content = create_content(client, bob, db_session, "bob private content")

    alice_doc = client.post(
        "/api/documents/from-content",
        headers=auth_header(alice),
        json={"content_id": alice_content, "category": "other"},
    ).json()
    bob_doc = client.post(
        "/api/documents/from-content",
        headers=auth_header(bob),
        json={"content_id": bob_content, "category": "other"},
    ).json()

    alice_list = client.get("/api/documents", headers=auth_header(alice))
    bob_get_alice = client.get(f"/api/documents/{alice_doc['id']}", headers=auth_header(bob))

    assert alice_list.status_code == 200
    assert [doc["id"] for doc in alice_list.json()] == [alice_doc["id"]]
    assert bob_get_alice.status_code == 404
    assert alice_doc["id"] != bob_doc["id"]


def test_delete_document_removes_only_current_user_document(client: TestClient, db_session: Session) -> None:
    token = register_and_login(client, "doc-delete@example.com")
    content_id = create_content(client, token, db_session, "delete me content")
    created = client.post(
        "/api/documents/from-content",
        headers=auth_header(token),
        json={"content_id": content_id, "category": "other"},
    )
    assert created.status_code == 201

    delete_response = client.delete(f"/api/documents/{created.json()['id']}", headers=auth_header(token))
    list_response = client.get("/api/documents", headers=auth_header(token))

    assert delete_response.status_code == 204
    assert list_response.status_code == 200
    assert list_response.json() == []
