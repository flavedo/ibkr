from zoneinfo import ZoneInfo

from apscheduler.schedulers.blocking import BlockingScheduler

from worker.jobs.daily_incremental_job import run_daily_incremental_job


def create_scheduler() -> BlockingScheduler:
    scheduler = BlockingScheduler(timezone=ZoneInfo("Asia/Shanghai"))
    scheduler.add_job(
        run_daily_incremental_job,
        trigger="cron",
        hour=9,
        minute=0,
        id="daily_incremental_job",
        replace_existing=True,
    )
    return scheduler
