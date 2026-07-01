from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.content import Content
from app.models.preference import UserPreference
from app.models.recommendation import Recommendation
from app.models.user import User
from app.repositories.push_logs import PushLogRepository
from app.services.push import RecommendationPushService
from app.tasks import jobs


def create_user_with_recommendation(db: Session, *, channel: str = "in_app") -> User:
    user = User(email=f"push-{channel}@example.com", password_hash=hash_password("password123"))
    db.add(user)
    db.flush()
    preference = UserPreference(
        user_id=user.id,
        interests=[],
        negative_interests=[],
        enabled_categories=["article"],
        push_channel=channel,
        push_email="push@example.com" if channel == "email" else None,
        dingtalk_webhook="https://example.com/webhook" if channel == "dingtalk" else None,
        daily_limit=5,
        language_preferences={},
    )
    content = Content(source_type="text", raw_text="push content", content_hash=f"hash-{channel}")
    db.add_all([preference, content])
    db.flush()
    recommendation = Recommendation(
        user_id=user.id,
        content_id=content.id,
        score=0.91,
        category="article",
        summary="值得阅读的内容",
        reason="匹配你的兴趣",
        tags=["AI"],
        status="pending",
    )
    db.add(recommendation)
    db.commit()
    db.refresh(user)
    return user


def test_in_app_daily_push_creates_push_log(db_session: Session) -> None:
    user = create_user_with_recommendation(db_session)

    result = RecommendationPushService(db_session).push_daily_recommendations(user.id)
    logs = PushLogRepository(db_session).list_for_user(user.id)

    assert result["status"] == "sent"
    assert result["recommendation_count"] == 1
    assert len(logs) == 1
    assert logs[0].channel == "in_app"
    assert logs[0].sent_at is not None


def test_email_push_skips_when_smtp_is_not_configured(db_session: Session) -> None:
    user = create_user_with_recommendation(db_session, channel="email")

    result = RecommendationPushService(db_session).push_daily_recommendations(user.id)

    assert result["status"] == "skipped"
    assert "SMTP" in result["message"]


def test_push_api_triggers_and_lists_logs(client) -> None:
    response = client.post("/api/auth/register", json={"email": "push-api@example.com", "password": "password123"})
    assert response.status_code == 201
    token = client.post("/api/auth/login", json={"email": "push-api@example.com", "password": "password123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/api/push/daily", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "skipped"

    response = client.get("/api/push/logs", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_push_daily_recommendations_task(monkeypatch, db_session: Session) -> None:
    user = create_user_with_recommendation(db_session)
    monkeypatch.setattr(jobs, "SessionLocal", lambda: db_session)

    result = jobs.push_daily_recommendations(str(user.id))

    assert result["status"] == "sent"


def test_push_daily_recommendations_for_active_users_queues_tasks(monkeypatch, db_session: Session) -> None:
    user = create_user_with_recommendation(db_session)
    monkeypatch.setattr(jobs, "SessionLocal", lambda: db_session)
    queued = []

    class FakeAsyncResult:
        id = "push-task-id"

    def fake_delay(user_id: str):
        queued.append(user_id)
        return FakeAsyncResult()

    monkeypatch.setattr(jobs.push_daily_recommendations, "delay", fake_delay)

    result = jobs.push_daily_recommendations_for_active_users(limit=10)

    assert result["queued"] == 1
    assert queued == [str(user.id)]


def test_push_schedule_contains_daily_push() -> None:
    from app.tasks.celery_app import celery_app

    assert "push-daily-recommendations-for-active-users" in celery_app.conf.beat_schedule


def test_disabled_push_channel_skips_and_records_log(db_session: Session) -> None:
    user = create_user_with_recommendation(db_session, channel="disabled")

    result = RecommendationPushService(db_session).push_daily_recommendations(user.id)
    logs = PushLogRepository(db_session).list_for_user(user.id)

    assert result["status"] == "skipped"
    assert result["channel"] == "disabled"
    assert "disabled" in result["message"]
    assert len(logs) == 1
    assert logs[0].status == "skipped"
    assert logs[0].sent_at is None


def test_daily_push_is_rate_limited_after_successful_send(db_session: Session) -> None:
    user = create_user_with_recommendation(db_session)
    service = RecommendationPushService(db_session)

    first = service.push_daily_recommendations(user.id)
    second = service.push_daily_recommendations(user.id)
    logs = PushLogRepository(db_session).list_for_user(user.id)

    assert first["status"] == "sent"
    assert second["status"] == "skipped"
    assert "Daily push limit" in second["message"]
    assert len(logs) == 2
    assert [log.status for log in logs] == ["skipped", "sent"]
