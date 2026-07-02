from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()
celery_app = Celery("personal_knowledge_radar", broker=str(settings.redis_url), backend=str(settings.redis_url))
celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone=settings.celery_timezone,
    enable_utc=False,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    result_expires=60 * 60 * 24,
    beat_schedule={
        "cleanup-failed-jobs": {
            "task": "cleanup_failed_jobs",
            "schedule": settings.celery_cleanup_interval_minutes * 60.0,
            "kwargs": {"older_than_minutes": 60, "limit": 100},
        },
        "cleanup-revoked-tokens": {
            "task": "cleanup_revoked_tokens",
            "schedule": settings.celery_cleanup_interval_minutes * 60.0,
            "kwargs": {"limit": 500},
        },
        "fetch-daily-sources-for-active-users": {
            "task": "fetch_daily_sources_for_active_users",
            "schedule": crontab(
                hour=settings.celery_daily_sources_hour,
                minute=settings.celery_daily_sources_minute,
            ),
            "kwargs": {"github_limit": 10, "limit": 100},
        },
        "push-daily-recommendations-for-active-users": {
            "task": "push_daily_recommendations_for_active_users",
            "schedule": crontab(
                hour=settings.celery_daily_sources_hour,
                minute=(settings.celery_daily_sources_minute + 10) % 60,
            ),
            "kwargs": {"limit": 100},
        },
    },
)

celery_app.autodiscover_tasks(["app.tasks"])
