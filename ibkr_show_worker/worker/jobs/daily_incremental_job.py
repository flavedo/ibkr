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
    clear_first: bool = False,
) -> dict:
    with tempfile.NamedTemporaryFile(prefix="ibkr_daily_", suffix=".csv", delete=False) as temp_file:
        downloaded_path = Path(temp_file.name)

    downloaded_file = flex_client.download_flex_statement(
        query_id=settings.flex_query_id_daily,
        save_path=downloaded_path,
    )

    if clear_first:
        all_indexes = [
            (settings.es_account_index, "accounts"),
            (settings.es_position_index, "positions"),
            (settings.es_trade_index, "trades"),
            (settings.es_cash_flow_index, "cash_flows"),
            (settings.es_price_history_index, "price_history"),
        ]
        for index_name, _ in all_indexes:
            try:
                es_writer.delete_by_query(index=index_name, body={"query": {"match_all": {}}})
            except Exception:
                pass

    return import_daily_snapshot_file(es_writer, downloaded_path)


def run_daily_incremental_job() -> dict:
    settings = get_settings()
    es_writer = ElasticsearchWriter(settings)
    flex_client = FlexClient(settings)
    return pull_daily_incremental(settings=settings, es_writer=es_writer, flex_client=flex_client, clear_first=True)
