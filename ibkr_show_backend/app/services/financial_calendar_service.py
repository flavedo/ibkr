import logging
from datetime import datetime

import yfinance as yf

from app.schemas.financial_calendar import (
    EarningsCalendarResponse,
    EarningsEvent,
    EconomicCalendarResponse,
    EconomicEvent,
)

logger = logging.getLogger(__name__)


class FinancialCalendarService:

    def get_earnings(self, start_date: str, end_date: str) -> EarningsCalendarResponse:
        cal = yf.Calendars(start=start_date, end=end_date)
        df = cal.get_earnings_calendar()

        items: list[EarningsEvent] = []
        for _, row in df.iterrows():
            date_val = row["Event Start Date"]
            date_str = date_val.strftime("%Y-%m-%d %H:%M") if hasattr(date_val, "strftime") else str(date_val)
            eps = row.get("EPS Estimate")
            reported = row.get("Reported EPS")
            surprise = row.get("Surprise(%)")
            cap = row.get("Marketcap")

            items.append(
                EarningsEvent(
                    company=str(row["Company"]),
                    marketcap=float(cap) if cap is not None and not _is_nan(cap) else None,
                    event_name=str(row["Event Name"]) if str(row["Event Name"]) != "nan" else None,
                    date_time=date_str,
                    timing=str(row.get("Timing", "")),
                    eps_estimate=float(eps) if eps is not None and not _is_nan(eps) else None,
                    reported_eps=float(reported) if reported is not None and not _is_nan(reported) else None,
                    surprise_pct=float(surprise) if surprise is not None and not _is_nan(surprise) else None,
                )
            )

        items.sort(key=lambda x: x.date_time or "")
        return EarningsCalendarResponse(items=items)

    def get_economic_events(self, start_date: str, end_date: str) -> EconomicCalendarResponse:
        cal = yf.Calendars(start=start_date, end=end_date)
        df = cal.get_economic_events_calendar()

        items: list[EconomicEvent] = []
        for _, row in df.iterrows():
            t = row["Event Time"]
            time_str = t.strftime("%Y-%m-%d %H:%M") if hasattr(t, "strftime") else str(t)
            actual = row.get("Actual")
            expected = row.get("Expected")
            last = row.get("Last")
            revised = row.get("Revised")

            items.append(
                EconomicEvent(
                    region=str(row["Region"]),
                    event_time=time_str,
                    for_period=str(row.get("For", "")),
                    actual=float(actual) if actual is not None and not _is_nan(actual) else None,
                    expected=float(expected) if expected is not None and not _is_nan(expected) else None,
                    last=float(last) if last is not None and not _is_nan(last) else None,
                    revised=float(revised) if revised is not None and not _is_nan(revised) else None,
                )
            )

        items.sort(key=lambda x: x.event_time or "")
        return EconomicCalendarResponse(items=items)


def _is_nan(v: object) -> bool:
    try:
        import math
        return math.isnan(float(v))
    except (TypeError, ValueError):
        return False
