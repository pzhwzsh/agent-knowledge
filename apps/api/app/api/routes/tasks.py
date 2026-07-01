from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User
from app.tasks.celery_app import celery_app

router = APIRouter()


@router.get("/health")
def task_health(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    inspector = celery_app.control.inspect(timeout=1.0)
    ping = inspector.ping() or {}
    stats = inspector.stats() or {}
    return {
        "broker_url": str(celery_app.conf.broker_url),
        "result_backend": str(celery_app.conf.result_backend),
        "workers_online": len(ping),
        "workers": sorted(ping.keys()),
        "stats_available": bool(stats),
    }


@router.get("/schedule")
def task_schedule(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    schedules = []
    for name, entry in celery_app.conf.beat_schedule.items():
        schedules.append(
            {
                "name": name,
                "task": entry["task"],
                "schedule": str(entry["schedule"]),
                "args": entry.get("args", []),
                "kwargs": entry.get("kwargs", {}),
            }
        )
    registered_tasks = sorted(
        task_name
        for task_name in celery_app.tasks.keys()
        if not task_name.startswith("celery.")
    )
    return {
        "timezone": celery_app.conf.timezone,
        "beat_schedule": schedules,
        "registered_tasks": registered_tasks,
    }
