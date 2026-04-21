from pathlib import Path
import tempfile

from worker.clients.es_client import ElasticsearchWriter
from worker.clients.flex_client import FlexClient
from worker.core.config import Settings, get_settings
from worker.jobs.import_daily_snapshot import import_daily_snapshot_file


def pull_daily_incremental(
    settings: Settings,
    es_writer: ElasticsearchWriter,
    flex_client: FlexClient,
) -> dict:
    if not settings.flex_query_id_daily:
        raise RuntimeError(
            "FLEX_QUERY_ID_DAILY is missing. Please fill it in ibkr_show_worker/.env before pulling from IBKR."
        )

    with tempfile.NamedTemporaryFile(prefix="ibkr_daily_", suffix=".csv", delete=False) as temp_file:
        downloaded_path = Path(temp_file.name)

    downloaded_file = flex_client.download_flex_statement(
        query_id=settings.flex_query_id_daily,
        save_path=downloaded_path,
    )
    return import_daily_snapshot_file(es_writer, downloaded_file)


def run_daily_incremental_job() -> dict:
    settings = get_settings()
    es_writer = ElasticsearchWriter(settings)
    flex_client = FlexClient(settings)
    return pull_daily_incremental(settings=settings, es_writer=es_writer, flex_client=flex_client)
