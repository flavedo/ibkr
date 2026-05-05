import logging
from functools import lru_cache

from forex_python.converter import CurrencyRates, RatesNotAvailableError

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_CURRENCY_MAP = {
    "CNH": "CNY",
}

_DEFAULT_FX_USD_CNH = 7.25


def _map_currency(code: str) -> str:
    return _CURRENCY_MAP.get(code, code)


@lru_cache(maxsize=32)
def get_live_rate(from_currency: str, to_currency: str) -> float | None:
    try:
        c = CurrencyRates()
        rate = c.get_rate(_map_currency(from_currency), _map_currency(to_currency))
        logger.info("Live rate %s/%s = %s", from_currency, to_currency, rate)
        return round(float(rate), 6)
    except RatesNotAvailableError:
        logger.warning("Rate %s/%s not available from forex-python", from_currency, to_currency)
        return None
    except Exception as exc:
        logger.warning("Failed to fetch rate %s/%s: %s", from_currency, to_currency, exc)
        return None


def get_exchange_rate(from_currency: str = "USD", to_currency: str = "CNH") -> float:
    live = get_live_rate(from_currency, to_currency)
    if live is not None:
        return live

    settings = get_settings()
    logger.info("Falling back to configured FX_USD_CNH = %s", settings.fx_usd_cnh)
    return settings.fx_usd_cnh
