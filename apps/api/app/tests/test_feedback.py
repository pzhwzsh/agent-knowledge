from fastapi.testclient import TestClient


def register_and_login(client: TestClient, email: str) -> str:
    response = client.post("/api/auth/register", json={"email": email, "password": "password123"})
    assert response.status_code == 201, response.text
    response = client.post("/api/auth/login", json={"email": email, "password": "password123"})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_user_can_create_and_list_feedback(client: TestClient) -> None:
    token = register_and_login(client, "feedback@example.com")

    created = client.post(
        "/api/feedback",
        headers=auth_header(token),
        json={
            "feature": "推荐",
            "feedback_type": "repair",
            "severity": "high",
            "message": "推荐结果重复，需要维修。",
        },
    )

    assert created.status_code == 201, created.text
    body = created.json()
    assert body["feature"] == "推荐"
    assert body["feedback_type"] == "repair"
    assert body["status"] == "open"

    listed = client.get("/api/feedback", headers=auth_header(token))

    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [body["id"]]


def test_feedback_is_isolated_by_current_user(client: TestClient) -> None:
    alice = register_and_login(client, "alice-feedback@example.com")
    bob = register_and_login(client, "bob-feedback@example.com")

    client.post(
        "/api/feedback",
        headers=auth_header(alice),
        json={"feature": "搜索", "feedback_type": "bug", "severity": "medium", "message": "搜索答案不准。"},
    )

    bob_feedback = client.get("/api/feedback", headers=auth_header(bob))

    assert bob_feedback.status_code == 200
    assert bob_feedback.json() == []


def test_feedback_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/feedback")

    assert response.status_code == 401
