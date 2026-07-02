from fastapi.testclient import TestClient


def register(client: TestClient, email: str, password: str = "password123") -> dict:
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "display_name": "Test User"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def login(client: TestClient, email: str, password: str = "password123") -> str:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_register_login_and_me(client: TestClient) -> None:
    user = register(client, "alice@example.com")
    token = login(client, "alice@example.com")

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["id"] == user["id"]
    assert response.json()["email"] == "alice@example.com"


def test_duplicate_email_is_rejected(client: TestClient) -> None:
    register(client, "alice@example.com")

    response = client.post(
        "/api/auth/register",
        json={"email": "alice@example.com", "password": "password123"},
    )

    assert response.status_code == 409


def test_preferences_are_isolated_by_current_user(client: TestClient) -> None:
    register(client, "alice@example.com")
    register(client, "bob@example.com")
    alice_token = login(client, "alice@example.com")
    bob_token = login(client, "bob@example.com")

    alice_update = client.put(
        "/api/preferences",
        headers={"Authorization": f"Bearer {alice_token}"},
        json={"interests": ["python", "security"], "daily_limit": 5},
    )
    assert alice_update.status_code == 200, alice_update.text

    bob_preferences = client.get(
        "/api/preferences",
        headers={"Authorization": f"Bearer {bob_token}"},
    )
    assert bob_preferences.status_code == 200
    assert bob_preferences.json()["interests"] == []
    assert bob_preferences.json()["daily_limit"] == 10

    alice_preferences = client.get(
        "/api/preferences",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert alice_preferences.status_code == 200
    assert alice_preferences.json()["interests"] == ["python", "security"]
    assert alice_preferences.json()["daily_limit"] == 5


def test_private_preferences_require_authentication(client: TestClient) -> None:
    response = client.get("/api/preferences")

    assert response.status_code == 401


def test_logout_revokes_current_token(client: TestClient) -> None:
    register(client, "logout@example.com")
    token = login(client, "logout@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    logout_response = client.post("/api/auth/logout", headers=headers)
    me_response = client.get("/api/auth/me", headers=headers)

    assert logout_response.status_code == 200, logout_response.text
    assert logout_response.json() == {"success": True}
    assert me_response.status_code == 401
