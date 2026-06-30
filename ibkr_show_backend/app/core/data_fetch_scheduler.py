import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.settings_service import load_settings

logger = logging.getLogger(__name__)

_JOB_ID = "data_fetch_daily"
_scheduler: BackgroundScheduler | None = None


def _run_data_fetch() -> None:
    """Execute the IBKR data refresh job."""
    logger.info("Scheduled data fetch started at %s", datetime.now(timezone.utc).isoformat())
    try:
        import sys
        sys.path.insert(0, "/app")
        from worker.jobs.daily_incremental_job import run_daily_incremental_job

        result = run_daily_incremental_job()
        logger.info("Scheduled data fetch completed: %s", result)
    except Exception as exc:
        logger.exception("Scheduled data fetch failed: %s", exc)


def _build_scheduler() -> BackgroundScheduler:
    sched = BackgroundScheduler(
        timezone=ZoneInfo("UTC"),
        job_defaults={"coalesce": True, "max_instances": 1},
    )
    return sched


def _schedule_fetch(scheduler: BackgroundScheduler, fetch_time: str) -> None:
    try:
        hour, minute = fetch_time.strip().split(":")
        trigger = CronTrigger(hour=int(hour), minute=int(minute), timezone=ZoneInfo("UTC"))
        scheduler.add_job(
            _run_data_fetch,
            trigger=trigger,
            id=_JOB_ID,
            replace_existing=True,
            name="Data fetch daily",
        )
        logger.info("Scheduled data fetch at %s UTC", fetch_time)
    except Exception as exc:
        logger.warning("Failed to schedule data fetch at %s: %s", fetch_time, exc)


def start_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        return

    _scheduler = _build_scheduler()
    settings = load_settings()
    if settings.fetch_enabled:
        _schedule_fetch(_scheduler, settings.fetch_time)
    else:
        logger.info("Data fetch is disabled, scheduler not activated")
    _scheduler.start()
    logger.info("Data fetch scheduler started")


def reschedule_fetch() -> None:
    if _scheduler is None:
        logger.warning("Scheduler not initialized, cannot reschedule")
        return

    settings = load_settings()
    if settings.fetch_enabled:
        _schedule_fetch(_scheduler, settings.fetch_time)
    else:
        _scheduler.remove_job(_JOB_ID)
        logger.info("Data fetch disabled, removed scheduled job")


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is None:
        return
    _scheduler.shutdown(wait=False)
    _scheduler = None
    logger.info("Data fetch scheduler stopped")
