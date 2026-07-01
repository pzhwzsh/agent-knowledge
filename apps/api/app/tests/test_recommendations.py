from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document


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


def create_content(client: TestClient, token: str, text: str = "python fastapi agent knowledge") -> str:
    response = client.post(
        "/api/ingestions",
        headers=auth_header(token),
        json={"input_type": "text", "input_value": text},
    )
    assert response.status_code == 200, response.text
    return response.json()["content"]["id"]


def test_generate_recommendation_does_not_create_document(
    client: TestClient,
    db_session: Session,
) -> None:
    token = register_and_login(client, "rec-generate@example.com")
    client.put(
        "/api/preferences",
        headers=auth_header(token),
        json={"interests": ["fastapi"], "enabled_categories": ["other"]},
    )
    content_id = create_content(client, token)

    response = client.post(
        "/api/recommendations/generate",
        headers=auth_header(token),
        json={"content_id": content_id},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "pending"
    assert body["score"] >= 50
    assert "fastapi" in body["tags"]
    assert list(db_session.scalars(select(Document))) == []


def test_recommendation_status_transitions(client: TestClient) -> None:
    token = register_and_login(client, "rec-status@example.com")
    content_id = create_content(client, token)
    recommendation = client.post(
        "/api/recommendations/generate",
        headers=auth_header(token),
        json={"content_id": content_id},
    ).json()

    ignored = client.post(
        f"/api/recommendations/{recommendation['id']}/ignore",
        headers=auth_header(token),
    )
    disliked = client.post(
        f"/api/recommendations/{recommendation['id']}/dislike",
        headers=auth_header(token),
    )

    assert ignored.status_code == 200
    assert ignored.json()["status"] == "ignored"
    assert disliked.status_code == 200
    assert disliked.json()["status"] == "disliked"


def test_save_recommendation_creates_document_idempotently(client: TestClient, db_session: Session) -> None:
    token = register_and_login(client, "rec-save@example.com")
    content_id = create_content(client, token, "save this fastapi article " * 20)
    recommendation = client.post(
        "/api/recommendations/generate",
        headers=auth_header(token),
        json={"content_id": content_id},
    ).json()

    first = client.post(f"/api/recommendations/{recommendation['id']}/save", headers=auth_header(token))
    second = client.post(f"/api/recommendations/{recommendation['id']}/save", headers=auth_header(token))

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json()["recommendation"]["status"] == "saved"
    assert first.json()["document"]["id"] == second.json()["document"]["id"]
    assert len(list(db_session.scalars(select(Document)))) == 1


def test_recommendations_are_isolated_by_current_user(client: TestClient) -> None:
    alice = register_and_login(client, "alice-rec@example.com")
    bob = register_and_login(client, "bob-rec@example.com")
    alice_content = create_content(client, alice, "alice recommendation content")
    bob_content = create_content(client, bob, "bob recommendation content")
    alice_rec = client.post(
        "/api/recommendations/generate",
        headers=auth_header(alice),
        json={"content_id": alice_content},
    ).json()
    bob_rec = client.post(
        "/api/recommendations/generate",
        headers=auth_header(bob),
        json={"content_id": bob_content},
    ).json()

    alice_list = client.get("/api/recommendations", headers=auth_header(alice))
    bob_save_alice = client.post(f"/api/recommendations/{alice_rec['id']}/save", headers=auth_header(bob))

    assert alice_list.status_code == 200
    assert [item["id"] for item in alice_list.json()] == [alice_rec["id"]]
    assert bob_save_alice.status_code == 404
    assert alice_rec["id"] != bob_rec["id"]
