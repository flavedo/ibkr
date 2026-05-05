import logging
from datetime import datetime, date
from typing import Any

import requests

from app.schemas.financial_calendar import EarningsCalendarResponse, EarningsEvent

logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

_SESSION: requests.Session | None = None
_CRUMB: str | None = None


def _get_session() -> requests.Session:
    global _SESSION
    if _SESSION is None:
        _SESSION = requests.Session()
        _SESSION.headers.update({"User-Agent": USER_AGENT})
    return _SESSION


def _get_crumb() -> str:
    global _CRUMB
    if _CRUMB:
        return _CRUMB
    s = _get_session()
    s.get("https://fc.yahoo.com/", timeout=10)
    r = s.get("https://query2.finance.yahoo.com/v1/test/getcrumb", timeout=10)
    _CRUMB = r.text.strip()
    return _CRUMB


def _screen_earnings(start_date: date, end_date: date) -> list[dict[str, Any]]:
    from_ts = int(datetime.combine(start_date, datetime.min.time()).timestamp())
    to_ts = int(datetime.combine(end_date, datetime.min.time()).timestamp())

    session = _get_session()
    crumb = _get_crumb()

    operands = [
        {"operator": "EQ", "operands": ["region", "us"]},
        {"operator": "GT", "operands": ["earningsTimestamp", str(from_ts)]},
        {"operator": "LT", "operands": ["earningsTimestamp", str(to_ts)]},
    ]

    body = {
        "offset": 0,
        "size": 250,
        "sortField": "intradaymarketcap",
        "sortType": "DESC",
        "quoteType": "EQUITY",
        "query": {"operator": "AND", "operands": operands},
    }

    url = f"https://query2.finance.yahoo.com/v1/finance/screener?crumb={crumb}"
    r = session.post(url, json=body, timeout=20)
    if r.status_code != 200:
        raise RuntimeError(f"Yahoo screener HTTP {r.status_code}")

    quotes = r.json().get("finance", {}).get("result", [{}])[0].get("quotes", [])
    result: list[dict[str, Any]] = []

    for q in quotes:
        ts = q.get("earningsTimestamp", 0)
        if not (ts and isinstance(ts, (int, float)) and ts > 0):
            continue
        d = datetime.fromtimestamp(ts).date()
        if not (start_date <= d <= end_date):
            continue

        mcap_raw = q.get("marketCap", 0)
        if isinstance(mcap_raw, dict):
            mcap_raw = mcap_raw.get("raw", 0)

        result.append({
            "symbol": q.get("symbol", ""),
            "name": (q.get("shortName") or q.get("longName") or "")[:50],
            "mcap": mcap_raw or 0,
            "exchange": q.get("exchange", ""),
            "earnings_timestamp": ts,
        })

    seen: set[str] = set()
    cleaned: list[dict[str, Any]] = []
    for item in sorted(result, key=lambda x: (
        x.get("mcap", 0) or 0,
        0 if x.get("exchange") in ("NYQ", "NMS") else 1
    ), reverse=True):
        sym = item["symbol"]
        if sym and sym not in seen:
            seen.add(sym)
            cleaned.append(item)
    return cleaned


def _fetch_earnings_detail(symbol: str) -> dict[str, Any] | None:
    session = _get_session()
    crumb = _get_crumb()
    url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}?modules=calendarEvents&crumb={crumb}"

    try:
        resp = session.get(url, timeout=10)
    except requests.RequestException:
        return None
    if resp.status_code != 200:
        return None

    try:
        ea = resp.json()["quoteSummary"]["result"][0]["calendarEvents"]["earnings"]
    except (KeyError, IndexError, TypeError):
        return None

    def _raw(d: dict, key: str) -> float | None:
        v = d.get(key, {})
        if isinstance(v, dict):
            raw = v.get("raw")
            return float(raw) if raw is not None else None
        return None

    def _fmt(d: dict, key: str) -> str:
        v = d.get(key, {})
        if isinstance(v, dict):
            return v.get("fmt", "") or ""
        return str(v) if v else ""

    ed_list = ea.get("earningsDate", [])
    date_str = _fmt(ed_list[0], "fmt") if ed_list else ""

    call_list = ea.get("earningsCallDate", [])
    call_str = _fmt(call_list[0], "fmt") if call_list else ""

    return {
        "date": date_str,
        "is_estimate": ea.get("isEarningsDateEstimate", True),
        "eps_avg": _raw(ea, "earningsAverage"),
        "eps_low": _raw(ea, "earningsLow"),
        "eps_high": _raw(ea, "earningsHigh"),
        "rev_avg": _raw(ea, "revenueAverage"),
        "rev_low": _raw(ea, "revenueLow"),
        "rev_high": _raw(ea, "revenueHigh"),
        "call_date": call_str,
    }


class FinancialCalendarService:

    def get_earnings(self, start_date: str, end_date: str) -> EarningsCalendarResponse:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)

        logger.info("Screen earnings %s ~ %s", start, end)
        stocks = _screen_earnings(start, end)
        logger.info("Found %d stocks via screener", len(stocks))

        if not stocks:
            return EarningsCalendarResponse(items=[])

        enriched: list[dict[str, Any]] = []
        for i, s in enumerate(stocks):
            sym = s["symbol"]
            detail = _fetch_earnings_detail(sym)
            if detail and detail.get("date"):
                enriched.append({**s, **detail})
            if (i + 1) % 10 == 0:
                logger.info("Fetched detail %d/%d", i + 1, len(stocks))

        enriched.sort(key=lambda x: (x.get("date", ""), -x.get("mcap", 0)))

        items = [
            EarningsEvent(
                symbol=item.get("symbol", ""),
                name=item.get("name", ""),
                mcap=item.get("mcap", 0),
                exchange=item.get("exchange", ""),
                date=item.get("date", ""),
                is_estimate=item.get("is_estimate", True),
                eps_avg=item.get("eps_avg"),
                eps_low=item.get("eps_low"),
                eps_high=item.get("eps_high"),
                rev_avg=item.get("rev_avg"),
                rev_low=item.get("rev_low"),
                rev_high=item.get("rev_high"),
                call_date=item.get("call_date", ""),
            )
            for item in enriched
        ]

        return EarningsCalendarResponse(items=items)
