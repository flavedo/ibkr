from worker.core.scheduler import create_scheduler


def test_create_scheduler_uses_1230_asia_shanghai() -> None:
    scheduler = create_scheduler()

    job = scheduler.get_job("daily_incremental_job")
    assert job is not None
    assert str(job.trigger) == "cron[hour='12', minute='30']"
    assert str(scheduler.timezone) == "Asia/Shanghai"
