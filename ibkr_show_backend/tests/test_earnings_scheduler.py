from unittest.mock import MagicMock, patch

from app.core.earnings_scheduler import _schedule_push, reschedule_push, start_scheduler, stop_scheduler
from app.schemas.earnings_settings import EarningsPushSettings


def test_schedule_push_adds_cron_job():
    scheduler = MagicMock()
    _schedule_push(scheduler, "09:30")
    assert scheduler.add_job.call_count == 1
    call_kwargs = scheduler.add_job.call_args.kwargs
    assert call_kwargs["id"] == "earnings_daily_push"
    assert call_kwargs["replace_existing"] is True
    trigger = call_kwargs["trigger"]
    assert "hour='9'" in str(trigger)
    assert "minute='30'" in str(trigger)


def test_schedule_push_handles_single_digit():
    scheduler = MagicMock()
    _schedule_push(scheduler, "08:05")
    trigger = scheduler.add_job.call_args.kwargs["trigger"]
    assert "hour='8'" in str(trigger)
    assert "minute='5'" in str(trigger)


def test_start_scheduler_disabled():
    with patch("app.core.earnings_scheduler.load_settings") as mock_load:
        mock_load.return_value = EarningsPushSettings(enabled=False)
        stop_scheduler()
        start_scheduler()
        from app.core.earnings_scheduler import _scheduler
        assert _scheduler is not None
        job = _scheduler.get_job("earnings_daily_push")
        assert job is None
        stop_scheduler()


def test_start_scheduler_enabled():
    with patch("app.core.earnings_scheduler.load_settings") as mock_load:
        mock_load.return_value = EarningsPushSettings(enabled=True, push_time="07:00")
        stop_scheduler()
        start_scheduler()
        from app.core.earnings_scheduler import _scheduler
        assert _scheduler is not None
        job = _scheduler.get_job("earnings_daily_push")
        assert job is not None
        assert "hour='7'" in str(job.trigger)
        assert "minute='0'" in str(job.trigger)
        stop_scheduler()


def test_reschedule_push_removes_job_when_disabled():
    with patch("app.core.earnings_scheduler.load_settings") as mock_load:
        mock_load.return_value = EarningsPushSettings(enabled=True, push_time="09:00")
        stop_scheduler()
        start_scheduler()
        from app.core.earnings_scheduler import _scheduler
        assert _scheduler is not None
        job = _scheduler.get_job("earnings_daily_push")
        assert job is not None

        mock_load.return_value = EarningsPushSettings(enabled=False)
        reschedule_push()
        job = _scheduler.get_job("earnings_daily_push")
        assert job is None
        stop_scheduler()


def test_reschedule_push_updates_time():
    with patch("app.core.earnings_scheduler.load_settings") as mock_load:
        mock_load.return_value = EarningsPushSettings(enabled=True, push_time="22:00")
        stop_scheduler()
        start_scheduler()
        from app.core.earnings_scheduler import _scheduler
        assert _scheduler is not None
        mock_load.return_value = EarningsPushSettings(enabled=True, push_time="23:30")
        reschedule_push()
        job = _scheduler.get_job("earnings_daily_push")
        assert job is not None
        assert "hour='23'" in str(job.trigger)
        assert "minute='30'" in str(job.trigger)
        stop_scheduler()
