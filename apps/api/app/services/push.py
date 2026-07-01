from uuid import UUID

from sqlalchemy.orm import Session

from app.models.preference import UserPreference
from app.models.recommendation import Recommendation
from app.repositories.preferences import PreferenceRepository
from app.repositories.push_logs import PushLogRepository
from app.repositories.recommendations import RecommendationRepository
from app.services.notifiers import DingTalkNotifier, EmailNotifier, NotificationResult


class RecommendationPushService:
    def __init__(
        self,
        db: Session,
        *,
        email_notifier: EmailNotifier | None = None,
        dingtalk_notifier: DingTalkNotifier | None = None,
    ) -> None:
        self.db = db
        self.preferences = PreferenceRepository(db)
        self.recommendations = RecommendationRepository(db)
        self.push_logs = PushLogRepository(db)
        self.email_notifier = email_notifier or EmailNotifier()
        self.dingtalk_notifier = dingtalk_notifier or DingTalkNotifier()

    def push_daily_recommendations(self, user_id: UUID) -> dict[str, object]:
        preference = self.preferences.get_by_user_id(user_id)
        if preference is None:
            return self._record(user_id, "in_app", "skipped", "User preference not found.", [])

        if preference.push_channel == "disabled":
            return self._record(user_id, "disabled", "skipped", "User has disabled recommendation pushes.", [])

        if self.push_logs.has_sent_today(user_id, channel=preference.push_channel):
            return self._record(user_id, preference.push_channel, "skipped", "Daily push limit already reached for this channel.", [])

        recommendations = self.recommendations.list_pending_for_push(user_id, limit=preference.daily_limit)
        if not recommendations:
            return self._record(user_id, preference.push_channel, "skipped", "No pending recommendations.", [])

        title = "个人信息雷达每日推荐"
        body = _render_recommendations(recommendations)
        result = self._send(preference, title, body)
        return self._record(
            user_id,
            preference.push_channel,
            result.status,
            result.message,
            recommendations,
            body=body,
        )

    def _send(self, preference: UserPreference, title: str, body: str) -> NotificationResult:
        if preference.push_channel == "email":
            if not preference.push_email:
                return NotificationResult(status="skipped", message="Push email is not configured.")
            return self.email_notifier.send(to_email=preference.push_email, subject=title, body=body)
        if preference.push_channel == "dingtalk":
            webhook = preference.dingtalk_webhook
            return self.dingtalk_notifier.send(webhook=webhook or "", text=f"{title}\n\n{body}")
        return NotificationResult(status="sent", message="In-app push log created.")

    def _record(
        self,
        user_id: UUID,
        channel: str,
        status: str,
        message: str,
        recommendations: list[Recommendation],
        *,
        body: str | None = None,
    ) -> dict[str, object]:
        log = self.push_logs.create(
            user_id=user_id,
            channel=channel,
            status=status,
            message=message,
            metadata_json={
                "recommendation_ids": [str(item.id) for item in recommendations],
                "body": body,
            },
            sent=status == "sent",
        )
        self.db.commit()
        return {
            "push_log_id": str(log.id),
            "channel": channel,
            "status": status,
            "message": message,
            "recommendation_count": len(recommendations),
        }


def _render_recommendations(recommendations: list[Recommendation]) -> str:
    lines = []
    for index, item in enumerate(recommendations, start=1):
        title = item.summary or item.reason or f"推荐内容 {item.content_id}"
        tags = ", ".join(item.tags) if item.tags else "无标签"
        lines.append(f"{index}. {title}\n   分类：{item.category}；评分：{item.score:.2f}；标签：{tags}")
    return "\n\n".join(lines)
