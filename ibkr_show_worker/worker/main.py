import argparse
import logging
from pathlib import Path

from worker.clients.es_client import ElasticsearchWriter
from worker.clients.flex_client import FlexClient, FlexClientError
from worker.core.config import get_settings
from worker.core.logger import configure_logging
from worker.core.scheduler import create_scheduler
from worker.jobs.daily_incremental_job import pull_daily_incremental
from worker.jobs.import_daily_snapshot import import_daily_snapshot_file

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="IBKR Show worker CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-es", help="Create Elasticsearch indices if they do not exist.")
    subparsers.add_parser("es-health", help="Check Elasticsearch cluster health.")

    import_daily = subparsers.add_parser(
        "import-daily-file",
        help="Import a local MyDailyData Flex CSV, including historical ranges.",
    )
    import_daily.add_argument("--file", required=True, help="Absolute path to a daily Flex CSV file.")

    subparsers.add_parser(
        "pull-daily-from-ibkr",
        help="Pull the configured MyDailyData Flex query from IBKR and ingest it into Elasticsearch.",
    )

    subparsers.add_parser(
        "run-scheduler",
        help="Run the daily scheduler. It pulls the MyDailyData query every day at 12:30 Asia/Shanghai and ingests it idempotently.",
    )

    return parser


def _require_file(file_path: str) -> Path:
    candidate = Path(file_path)
    if not candidate.is_file():
        raise FileNotFoundError(f"CSV file does not exist: {candidate}")
    return candidate


def main() -> None:
    configure_logging()
    settings = get_settings()
    args = build_parser().parse_args()
    es_writer = ElasticsearchWriter(settings)

    if args.command == "init-es":
        results = es_writer.initialize_indices()
        for item in results:
            logger.info("index=%s created=%s", item["index"], item["created"])
        return

    if args.command == "es-health":
        health = es_writer.health()
        logger.info("elasticsearch health: %s", health)
        return

    if args.command == "import-daily-file":
        result = import_daily_snapshot_file(es_writer, _require_file(args.file))
        logger.info("daily import result: %s", result)
        return

    if args.command == "pull-daily-from-ibkr":
        flex_client = FlexClient(settings)
        try:
            result = pull_daily_incremental(
                settings=settings,
                es_writer=es_writer,
                flex_client=flex_client,
            )
            logger.info("pulled daily statement and imported: %s", result)
        except FlexClientError as exc:
            logger.error("pull-daily-from-ibkr failed: %s", exc)
            raise SystemExit(1) from exc
        return

    if args.command == "run-scheduler":
        scheduler = create_scheduler()
        logger.info("starting scheduler; daily MyDailyData incremental job runs daily at 12:30 Asia/Shanghai")
        scheduler.start()
        return


if __name__ == "__main__":
    main()
