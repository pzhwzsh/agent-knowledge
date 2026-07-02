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


def promote_to_admin(email: str) -> None:
    from app.tests.conftest import TestingSessionLocal
    from app.models.user import User
    with TestingSessionLocal() as db:
        user = db.query(User).filter(User.email == email).one()
        user.is_admin = True
        db.add(user)
        db.commit()


def test_feedback_admin_can_list_and_update_status(client: TestClient) -> None:
    user_token = register_and_login(client, "feedback-user@example.com")
    admin_email = "feedback-admin@example.com"
    admin_token = register_and_login(client, admin_email)
    promote_to_admin(admin_email)
    admin_token = client.post("/api/auth/login", json={"email": admin_email, "password": "password123"}).json()["access_token"]

    created = client.post(
        "/api/feedback",
        headers=auth_header(user_token),
        json={"feature": "采集", "feedback_type": "delete", "severity": "high", "message": "这个入口不好用。"},
    ).json()

    listed = client.get("/api/feedback/admin/all", headers=auth_header(admin_token))
    updated = client.patch(
        f"/api/feedback/admin/{created['id']}",
        headers=auth_header(admin_token),
        json={"status": "planned", "metadata_json": {"admin_note": "排入维修计划"}},
    )

    assert listed.status_code == 200
    assert any(item["id"] == created["id"] for item in listed.json())
    assert updated.status_code == 200, updated.text
    assert updated.json()["status"] == "planned"
    assert updated.json()["metadata_json"]["admin_note"] == "排入维修计划"

    from app.models.logs import AuditLog
    from app.tests.conftest import TestingSessionLocal

    with TestingSessionLocal() as db:
        actions = [log.action for log in db.query(AuditLog).order_by(AuditLog.created_at).all()]
    assert "feedback_admin_list" in actions
    assert "feedback_status_update" in actions


def test_feedback_admin_endpoints_forbid_non_admin(client: TestClient) -> None:
    token = register_and_login(client, "feedback-not-admin@example.com")

    response = client.get("/api/feedback/admin/all", headers=auth_header(token))

    assert response.status_code == 403
