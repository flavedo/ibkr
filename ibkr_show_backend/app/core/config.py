from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import os

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


def _is_production(app_env: str) -> bool:
    return app_env.strip().lower() in {"prod", "production"}


def _read_bool(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _read_string(
    name: str,
    default: str,
    *,
    app_env: str,
    require_explicit_in_prod: bool = False,
    forbidden_prod_values: set[str] | None = None,
) -> str:
    raw_value = os.getenv(name)
    value = raw_value if raw_value is not None else default

    if require_explicit_in_prod and _is_production(app_env) and raw_value is None:
        raise RuntimeError(f"{name} must be set explicitly when APP_ENV is production.")

    forbidden_values = forbidden_prod_values or set()
    if _is_production(app_env) and value in forbidden_values:
        raise RuntimeError(f"{name} cannot use the public placeholder value when APP_ENV is production.")

    return value


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_env: str
    app_host: str
    app_port: int
    cors_allow_origins: str
    cors_allow_origin_regex: str
    auth_username: str
    auth_password: str
    auth_session_secret: str
    auth_session_max_age_seconds: int
    es_host: str
    es_username: str
    es_password: str
    es_verify_certs: bool
    es_account_index: str
    es_position_index: str
    es_trade_index: str
    es_cash_flow_index: str
    es_price_history_index: str


@lru_cache
def get_settings() -> Settings:
    app_env = os.getenv("APP_ENV", "dev")
    return Settings(
        app_name=os.getenv("APP_NAME", "ibkr_show_backend"),
        app_env=app_env,
        app_host=os.getenv("APP_HOST", "0.0.0.0"),
        app_port=int(os.getenv("APP_PORT", "8000")),
        cors_allow_origins=os.getenv(
            "CORS_ALLOW_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ),
        cors_allow_origin_regex=os.getenv("CORS_ALLOW_ORIGIN_REGEX", r"https?://.*"),
        auth_username=_read_string(
            "AUTH_USERNAME",
            "admin",
            app_env=app_env,
            require_explicit_in_prod=True,
        ),
        auth_password=_read_string(
            "AUTH_PASSWORD",
            "change-me",
            app_env=app_env,
            require_explicit_in_prod=True,
            forbidden_prod_values={"change-me"},
        ),
        auth_session_secret=_read_string(
            "AUTH_SESSION_SECRET",
            "change-me-session-secret",
            app_env=app_env,
            require_explicit_in_prod=True,
            forbidden_prod_values={"change-me-session-secret"},
        ),
        auth_session_max_age_seconds=int(os.getenv("AUTH_SESSION_MAX_AGE_SECONDS", "604800")),
        es_host=os.getenv("ES_HOST", "http://localhost:9200"),
        es_username=os.getenv("ES_USERNAME", ""),
        es_password=os.getenv("ES_PASSWORD", ""),
        es_verify_certs=_read_bool("ES_VERIFY_CERTS", False),
        es_account_index=os.getenv("ES_ACCOUNT_INDEX", "ibkr_account_daily_snapshot_v1"),
        es_position_index=os.getenv("ES_POSITION_INDEX", "ibkr_position_daily_snapshot_v1"),
        es_trade_index=os.getenv("ES_TRADE_INDEX", "ibkr_trade_records_v1"),
        es_cash_flow_index=os.getenv("ES_CASH_FLOW_INDEX", "ibkr_cash_flow_records_v1"),
        es_price_history_index=os.getenv("ES_PRICE_HISTORY_INDEX", "ibkr_symbol_price_history_v1"),
    )
