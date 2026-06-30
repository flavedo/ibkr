import json
import logging
from pathlib import Path

from app.schemas.settings import SystemSettings

logger = logging.getLogger(__name__)

_CONFIG_DIR = Path(__file__).resolve().parents[2] / "data"
_CONFIG_FILE = _CONFIG_DIR / "system_settings.json"


def _ensure_config_dir() -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_settings() -> SystemSettings:
    _ensure_config_dir()
    if not _CONFIG_FILE.exists():
        return SystemSettings()
    try:
        data = json.loads(_CONFIG_FILE.read_text())
        return SystemSettings(**data)
    except (json.JSONDecodeError, TypeError) as exc:
        logger.warning("Failed to load settings: %s", exc)
        return SystemSettings()


def save_settings(settings: SystemSettings) -> SystemSettings:
    _ensure_config_dir()
    _CONFIG_FILE.write_text(settings.model_dump_json(indent=2))
    logger.info("System settings saved")

    from app.core.earnings_scheduler import reschedule_push
    reschedule_push()

    from app.core.data_fetch_scheduler import reschedule_fetch
    reschedule_fetch()

    return settings
