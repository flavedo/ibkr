from forex_python.converter import CurrencyRates, RatesNotAvailableError

from app.services.exchange_rate_service import _map_currency, get_exchange_rate, get_live_rate


def test_map_currency_maps_cnh_to_cny():
    assert _map_currency("CNH") == "CNY"
    assert _map_currency("CNY") == "CNY"
    assert _map_currency("USD") == "USD"
    assert _map_currency("EUR") == "EUR"
    assert _map_currency("HKD") == "HKD"


def test_get_live_rate_returns_valid_rate():
    rate = get_live_rate("USD", "CNH")
    assert rate is not None
    assert isinstance(rate, float)
    assert rate > 1.0
    assert rate < 15.0


def test_get_live_rate_different_pairs():
    usd_eur = get_live_rate("USD", "EUR")
    assert usd_eur is not None
    assert 0.5 < usd_eur < 1.5

    eur_usd = get_live_rate("EUR", "USD")
    assert eur_usd is not None
    assert 0.8 < eur_usd < 2.0


def test_get_live_rate_invalid_currency_returns_none():
    rate = get_live_rate("USD", "ZZZ")
    assert rate is None


def test_get_exchange_rate_returns_live_rate():
    rate = get_exchange_rate("USD", "CNH")
    assert isinstance(rate, float)
    assert rate > 1.0
    assert rate < 15.0


def test_get_exchange_rate_reverse():
    rate = get_exchange_rate("CNH", "USD")
    assert isinstance(rate, float)
    assert 0.05 < rate < 0.5


def test_forex_python_directly():
    c = CurrencyRates()
    rate = c.get_rate("USD", "CNY")
    assert isinstance(rate, float)
    assert rate > 1.0
    expected_min = 6.0
    expected_max = 8.0
    assert expected_min < rate < expected_max, (
        f"USD/CNY rate {rate} outside expected range ({expected_min}-{expected_max})"
    )
