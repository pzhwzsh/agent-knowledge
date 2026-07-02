from fastapi.testclient import TestClient

from app.models.logs import AuditLog
from app.models.user import User
from app.tests.conftest import TestingSessionLocal


def register_and_login(client: TestClient, email: str, *, is_admin: bool = False) -> str:
    response = client.post("/api/auth/register", json={"email": email, "password": "password123"})
    assert response.status_code == 201, response.text
    if is_admin:
        with TestingSessionLocal() as db:
            user = db.query(User).filter(User.email == email).one()
            user.is_admin = True
            db.add(user)
            db.commit()
    response = client.post("/api/auth/login", json={"email": email, "password": "password123"})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_admin_can_list_audit_logs(client: TestClient) -> None:
    admin_token = register_and_login(client, "audit-admin@example.com", is_admin=True)

    response = client.get("/api/audit/logs", headers=auth_header(admin_token))

    assert response.status_code == 200, response.text
    body = response.json()
    assert any(item["action"] == "audit_log_list" for item in body)


def test_admin_can_filter_audit_logs(client: TestClient) -> None:
    admin_token = register_and_login(client, "audit-filter-admin@example.com", is_admin=True)
    with TestingSessionLocal() as db:
        admin = db.query(User).filter(User.email == "audit-filter-admin@example.com").one()
        db.add(AuditLog(user_id=admin.id, action="custom_action", resource_type="custom_resource", metadata_json={"ok": True}))
        db.commit()

    response = client.get("/api/audit/logs?action=custom_action", headers=auth_header(admin_token))

    assert response.status_code == 200, response.text
    body = response.json()
    assert [item["action"] for item in body] == ["custom_action"]
    assert body[0]["metadata_json"] == {"ok": True}


def test_audit_logs_forbid_non_admin(client: TestClient) -> None:
    token = register_and_login(client, "audit-user@example.com")

    response = client.get("/api/audit/logs", headers=auth_header(token))

    assert response.status_code == 403
