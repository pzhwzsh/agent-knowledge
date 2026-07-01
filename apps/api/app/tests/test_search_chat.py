from fastapi.testclient import TestClient


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


def ingest_document(client: TestClient, token: str, text: str, category: str = "learning") -> dict:
    ingestion = client.post(
        "/api/ingestions",
        headers=auth_header(token),
        json={"input_type": "text", "input_value": text},
    )
    assert ingestion.status_code == 200, ingestion.text
    content_id = ingestion.json()["content"]["id"]
    document = client.post(
        "/api/documents/from-content",
        headers=auth_header(token),
        json={"content_id": content_id, "category": category, "tags": [category]},
    )
    assert document.status_code == 201, document.text
    return document.json()


def test_semantic_search_returns_current_user_chunks_only(client: TestClient) -> None:
    alice = register_and_login(client, "alice-search@example.com")
    bob = register_and_login(client, "bob-search@example.com")
    ingest_document(client, alice, "python vector database fastapi knowledge retrieval " * 20)
    ingest_document(client, bob, "travel island hotel food beach " * 20)

    response = client.post(
        "/api/search",
        headers=auth_header(alice),
        json={"query": "fastapi retrieval", "limit": 5},
    )

    assert response.status_code == 200, response.text
    results = response.json()["results"]
    assert results
    assert all("travel island" not in result["content"] for result in results)


def test_chat_returns_answer_with_citations(client: TestClient) -> None:
    token = register_and_login(client, "chat@example.com")
    document = ingest_document(client, token, "??????????????????????" * 20)

    response = client.post(
        "/api/chat",
        headers=auth_header(token),
        json={"question": "?????", "limit": 3},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert "??" in body["answer"]
    assert "??" in body["answer"]
    assert "??" in body["answer"]
    assert body["citations"]
    assert body["citations"][0]["document_id"] == document["id"]


def test_chat_unknown_when_user_has_no_chunks(client: TestClient) -> None:
    token = register_and_login(client, "empty-chat@example.com")

    response = client.post(
        "/api/chat",
        headers=auth_header(token),
        json={"question": "??????", "limit": 3},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["citations"] == []
    assert body["related_documents"] == []
    assert body["answer"].startswith("???")


def test_search_requires_authentication(client: TestClient) -> None:
    response = client.post("/api/search", json={"query": "test"})

    assert response.status_code == 401
