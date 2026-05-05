import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.earnings_settings_service import (
    load_settings,
    trigger_daily_push,
)

logger = logging.getLogger(__name__)

_JOB_ID = "earnings_daily_push"
_scheduler: BackgroundScheduler | None = None


def _build_scheduler() -> BackgroundScheduler:
    sched = BackgroundScheduler(
        timezone=ZoneInfo("Asia/Shanghai"),
        job_defaults={"coalesce": True, "max_instances": 1},
    )
    return sched


def _schedule_push(scheduler: BackgroundScheduler, push_time: str) -> None:
    try:
        hour, minute = push_time.strip().split(":")
        trigger = CronTrigger(hour=int(hour), minute=int(minute), timezone=ZoneInfo("Asia/Shanghai"))
        scheduler.add_job(
            trigger_daily_push,
            trigger=trigger,
            id=_JOB_ID,
            replace_existing=True,
            name="Earnings daily push",
        )
        logger.info("Scheduled earnings push at %s Asia/Shanghai", push_time)
    except Exception as exc:
        logger.warning("Failed to schedule push at %s: %s", push_time, exc)


def start_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        return

    _scheduler = _build_scheduler()
    settings = load_settings()
    if settings.enabled:
        _schedule_push(_scheduler, settings.push_time)
    else:
        logger.info("Earnings push is disabled, scheduler not activated")
    _scheduler.start()
    logger.info("Earnings push scheduler started")


def reschedule_push() -> None:
    if _scheduler is None:
        logger.warning("Scheduler not initialized, cannot reschedule")
        return

    settings = load_settings()
    if settings.enabled:
        _schedule_push(_scheduler, settings.push_time)
    else:
        _scheduler.remove_job(_JOB_ID)
        logger.info("Earnings push disabled, removed scheduled job")


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is None:
        return
    _scheduler.shutdown(wait=False)
    _scheduler = None
    logger.info("Earnings push scheduler stopped")
