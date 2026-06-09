"""
Macro Event Service

Provides US major economic events calendar data including:
- NFP (Non-farm Payrolls) - 非农就业数据
- CPI - 消费者物价指数
- FOMC Meetings - 美联储议息会议
- PPI - 生产者物价指数
- GDP - 国内生产总值
- Unemployment Rate - 失业率
- Retail Sales - 零售销售

Data source: Generated from known US economic release schedules,
supplemented by yfinance Calendars where available.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any

from app.schemas.financial_calendar import MacroEvent, MacroEventResponse

logger = logging.getLogger(__name__)

# FOMC meetings typically follow an 8-meeting-per-year schedule.
# Known meeting months: Jan, Mar, May, Jun, Jul, Sep, Nov, Dec
# The exact dates vary yearly. Approximate schedule for known years.
FOMC_SCHEDULE: dict[int, list[tuple[int, int, int]]] = {
    2026: [
        (1, 27, 28),   # Jan 27-28
        (3, 17, 18),   # Mar 17-18
        (5, 6, 7),     # May 6-7
        (6, 16, 17),   # Jun 16-17
        (7, 28, 29),   # Jul 28-29
        (9, 15, 16),   # Sep 15-16
        (11, 3, 4),    # Nov 3-4
        (12, 15, 16),  # Dec 15-16
    ],
    2027: [
        (1, 26, 27),
        (3, 16, 17),
        (5, 4, 5),
        (6, 15, 16),
        (7, 27, 28),
        (9, 21, 22),
        (11, 2, 3),
        (12, 14, 15),
    ],
}

MAJOR_EVENTS: dict[str, tuple[str, str, str, int]] = {
    "nfp": ("非农就业数据", "NFP", "美国非农就业报告", "high"),
    "cpi": ("消费者物价指数", "CPI", "美国CPI通胀数据", "high"),
    "fomc": ("美联储议息会议", "FOMC", "美联储FOMC利率决议", "high"),
    "ppi": ("生产者物价指数", "PPI", "美国PPI生产者物价指数", "medium"),
    "gdp": ("国内生产总值", "GDP", "美国GDP数据", "high"),
    "unemployment": ("失业率", "Unemployment", "美国失业率数据", "high"),
    "retail_sales": ("零售销售", "Retail Sales", "美国零售销售月率", "medium"),
}


def _first_friday_of_month(year: int, month: int) -> date:
    """Calculate the first Friday of a given month."""
    first_day = date(year, month, 1)
    # weekday(): Monday=0, ..., Friday=4, Saturday=5, Sunday=6
    days_ahead = 4 - first_day.weekday()  # 4 = Friday
    if days_ahead < 0:
        days_ahead += 7
    return first_day + timedelta(days=days_ahead)


def _nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> date:
    """Get the nth occurrence of a weekday (0=Mon, 6=Sun) in a month."""
    first_day = date(year, month, 1)
    days_ahead = weekday - first_day.weekday()
    if days_ahead < 0:
        days_ahead += 7
    return first_day + timedelta(days=days_ahead + (n - 1) * 7)


def _generate_nfp_events(year: int) -> list[dict[str, Any]]:
    """Generate NFP (Non-farm Payrolls) events for a given year.
    Released on the first Friday of each month at 8:30 AM ET.
    """
    events: list[dict[str, Any]] = []
    month_names = [
        "一月", "二月", "三月", "四月", "五月", "六月",
        "七月", "八月", "九月", "十月", "十一月", "十二月",
    ]
    for m in range(1, 13):
        release_date = _first_friday_of_month(year, m)
        events.append({
            "date": release_date.isoformat(),
            "title": f"非农就业数据 (NFP)",
            "type": "nfp",
            "importance": "high",
            "description": f"{year}年{month_names[m-1]}美国非农就业报告",
            "time": "08:30",
        })
    return events


def _generate_cpi_events(year: int) -> list[dict[str, Any]]:
    """Generate CPI events for a given year.
    CPI is typically released between the 10th and 15th of each month.
    Using a heuristic: ~13th, adjusted for weekends.
    """
    events: list[dict[str, Any]] = []
    month_names = [
        "一月", "二月", "三月", "四月", "五月", "六月",
        "七月", "八月", "九月", "十月", "十一月", "十二月",
    ]
    for m in range(1, 13):
        # Target the 13th, adjust to nearest weekday if weekend
        target = date(year, m, 13)
        if target.weekday() == 5:  # Saturday
            target = date(year, m, 14)
        elif target.weekday() == 6:  # Sunday
            target = date(year, m, 14)
        events.append({
            "date": target.isoformat(),
            "title": "消费者物价指数 (CPI)",
            "type": "cpi",
            "importance": "high",
            "description": f"{year}年{month_names[m-1]}美国CPI通胀数据",
            "time": "08:30",
        })
    return events


def _generate_fomc_events(year: int) -> list[dict[str, Any]]:
    """Generate FOMC meeting events.
    FOMC meetings usually span 2 days (Tue-Wed), with the decision released
    on the second day at 2:00 PM ET.
    """
    events: list[dict[str, Any]] = []
    schedule = FOMC_SCHEDULE.get(year, [])
    for month, start_day, end_day in schedule:
        end_date = date(year, month, end_day)
        events.append({
            "date": end_date.isoformat(),
            "title": "美联储议息会议 (FOMC)",
            "type": "fomc",
            "importance": "high",
            "description": f"美联储FOMC{year}年{month}月利率决议 (会议: {month}/{start_day}-{end_day})",
            "time": "14:00",
        })
    return events


def _generate_other_events(year: int) -> list[dict[str, Any]]:
    """Generate other major US economic events."""
    events: list[dict[str, Any]] = []
    month_names = [
        "一月", "二月", "三月", "四月", "五月", "六月",
        "七月", "八月", "九月", "十月", "十一月", "十二月",
    ]

    # PPI - typically released a day after CPI, around 11th-16th
    for m in range(1, 13):
        target = date(year, m, 14)
        if target.weekday() >= 5:
            target = date(year, m, 15)
        events.append({
            "date": target.isoformat(),
            "title": "生产者物价指数 (PPI)",
            "type": "ppi",
            "importance": "medium",
            "description": f"{year}年{month_names[m-1]}美国PPI生产者物价指数",
            "time": "08:30",
        })

    # GDP (quarterly) - Jan, Apr, Jul, Oct, around 25th-30th
    gdp_months = [1, 4, 7, 10]
    gdp_labels = ["Q4", "Q1", "Q2", "Q3"]
    gdp_desc = ["第四季度", "第一季度", "第二季度", "第三季度"]
    for i, m in enumerate(gdp_months):
        target = date(year, m, 28)
        if target.weekday() >= 5:
            target = date(year, m, 29)
        events.append({
            "date": target.isoformat(),
            "title": "国内生产总值 (GDP)",
            "type": "gdp",
            "importance": "high",
            "description": f"{year}年{gdp_desc[i]}美国GDP数据 ({gdp_labels[i]})",
            "time": "08:30",
        })

    # Unemployment rate - same day as NFP (first Friday)
    for m in range(1, 13):
        release_date = _first_friday_of_month(year, m)
        events.append({
            "date": release_date.isoformat(),
            "title": "失业率 (Unemployment Rate)",
            "type": "unemployment",
            "importance": "high",
            "description": f"{year}年{month_names[m-1]}美国失业率数据",
            "time": "08:30",
        })

    # Retail sales - around 14th-17th of each month
    for m in range(1, 13):
        target = date(year, m, 15)
        if target.weekday() >= 5:
            target = date(year, m, 16)
        events.append({
            "date": target.isoformat(),
            "title": "零售销售 (Retail Sales)",
            "type": "retail_sales",
            "importance": "medium",
            "description": f"{year}年{month_names[m-1]}美国零售销售月率",
            "time": "08:30",
        })

    return events


def _try_fetch_yfinance_events(start_date: date, end_date: date) -> list[dict[str, Any]]:
    """Try to fetch economic events from yfinance Calendars.
    Returns empty list on failure (non-critical).
    """
    try:
        import yfinance as yf
        calendars = yf.Calendars(
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d"),
        )
        data = calendars.get_economic_events_calendar()
        if data is None:
            return []

        events: list[dict[str, Any]] = []
        if hasattr(data, 'to_dict'):
            records = data.to_dict('records')
            for record in records:
                event_date = record.get("Event Time") or record.get("date") or ""
                if isinstance(event_date, datetime):
                    event_date = event_date.strftime("%Y-%m-%d")
                elif isinstance(event_date, date):
                    event_date = event_date.isoformat()

                if not event_date:
                    continue

                title = record.get("Event Name") or record.get("title") or ""
                region = record.get("Region") or record.get("region") or ""

                events.append({
                    "date": event_date,
                    "title": f"{title} ({region})" if region and region != "US" else title,
                    "type": "other",
                    "importance": "low",
                    "description": f"经济事件: {title}",
                    "time": None,
                    "actual": str(record.get("Actual") or "") if record.get("Actual") else None,
                    "expected": str(record.get("Expected") or "") if record.get("Expected") else None,
                    "previous": str(record.get("Last") or "") if record.get("Last") else None,
                })
        return events
    except Exception as exc:
        logger.warning("yfinance economic calendar fetch failed: %s", exc)
        return []


class MacroEventService:

    def get_events(self, start_date: str, end_date: str) -> MacroEventResponse:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)

        all_events: list[dict[str, Any]] = []

        # 1. Generate curated US major events for relevant years
        for year in range(start.year, end.year + 1):
            all_events.extend(_generate_nfp_events(year))
            all_events.extend(_generate_cpi_events(year))
            all_events.extend(_generate_fomc_events(year))
            all_events.extend(_generate_other_events(year))

        # 2. Try to supplement with yfinance data
        try:
            yf_events = _try_fetch_yfinance_events(start, end)
            all_events.extend(yf_events)
        except Exception as exc:
            logger.warning("Failed to fetch yfinance events: %s", exc)

        # 3. Filter by date range and deduplicate
        seen: set[tuple[str, str]] = set()
        filtered: list[dict[str, Any]] = []
        for evt in sorted(all_events, key=lambda x: x["date"]):
            evt_date = evt.get("date", "")
            evt_title = evt.get("title", "")
            key = (evt_date, evt_title)
            if key not in seen:
                try:
                    d = date.fromisoformat(evt_date)
                    if start <= d <= end:
                        seen.add(key)
                        filtered.append(evt)
                except (ValueError, TypeError):
                    continue

        return MacroEventResponse(
            items=[
                MacroEvent(**evt)
                for evt in filtered
            ]
        )