from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def run_sample_job() -> None:
    logger.info("sample worker job executed")
    logger.info("current time: %s", datetime.now().isoformat())
