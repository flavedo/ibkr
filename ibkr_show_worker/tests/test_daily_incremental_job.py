import pytest

from worker.clients.flex_client import FlexClient
from worker.core.config import Settings
from worker.jobs.daily_incremental_job import pull_daily_incremental


class DummyWriter:
    pass


def test_pull_daily_incremental_requires_query_id() -> None:
    settings = Settings(
        app_env="dev",
        flex_base_url="https://example.com",
        flex_token="token",
        flex_query_id_daily="",
        flex_user_agent="ibkr-show-worker/0.1",
        flex_poll_interval_seconds=5,
        flex_max_poll_retries=12,
        es_host="http://localhost:9200",
        es_username="",
        es_password="",
        es_verify_certs=False,
    )

    with pytest.raises(RuntimeError, match="FLEX_QUERY_ID_DAILY is missing"):
        pull_daily_incremental(
            settings=settings,
            es_writer=DummyWriter(),
            flex_client=FlexClient(settings),
        )
