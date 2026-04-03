from __future__ import annotations

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.database import SessionLocal
from app.models.preference import UserPreference
from app.models.user import User

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _run_digest_for_user(user_id_str: str) -> None:
    from app.tasks.pipeline import generate_user_digest
    import uuid

    db = SessionLocal()
    try:
        generate_user_digest(uuid.UUID(user_id_str), db)
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Scheduled digest failed for user %s: %s", user_id_str, exc, exc_info=True)
    finally:
        db.close()


def _schedule_all_users() -> None:
    """Refresh per-user digest jobs based on their delivery_time preference."""
    global _scheduler
    if _scheduler is None:
        return

    db = SessionLocal()
    try:
        users_prefs = (
            db.query(User, UserPreference)
            .join(UserPreference, UserPreference.user_id == User.id, isouter=True)
            .filter(User.is_active == True)  # noqa: E712
            .all()
        )
    finally:
        db.close()

    existing_job_ids = {job.id for job in _scheduler.get_jobs()}

    for user, pref in users_prefs:
        job_id = f"digest_{user.id}"
        delivery = pref.delivery_time if pref else None
        hour = delivery.hour if delivery else 8
        minute = delivery.minute if delivery else 0

        if job_id in existing_job_ids:
            _scheduler.reschedule_job(
                job_id, trigger=CronTrigger(hour=hour, minute=minute)
            )
        else:
            _scheduler.add_job(
                _run_digest_for_user,
                trigger=CronTrigger(hour=hour, minute=minute),
                id=job_id,
                args=[str(user.id)],
                replace_existing=True,
                misfire_grace_time=3600,
            )
            logger.info(
                "Scheduled digest job for user %s at %02d:%02d", user.id, hour, minute
            )


def start_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        return _scheduler

    _scheduler = BackgroundScheduler(timezone="UTC")

    # Re-schedule all users every hour to pick up preference changes
    _scheduler.add_job(
        _schedule_all_users,
        trigger=CronTrigger(minute=0),
        id="refresh_schedules",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info("APScheduler started")

    # Eagerly schedule existing users
    _schedule_all_users()
    return _scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped")
