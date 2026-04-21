from datetime import UTC, date, datetime, timedelta


DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%Y%m%d",
    "%m/%d/%Y",
)

DATETIME_FORMATS = (
    "%Y%m%d;%H%M%S",
    "%Y%m%d;%H%M",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y/%m/%d %H:%M:%S",
    "%Y/%m/%d %H:%M",
    "%Y-%m-%d,%H:%M:%S",
    "%Y-%m-%d,%H:%M",
    "%Y/%m/%d,%H:%M:%S",
    "%Y/%m/%d,%H:%M",
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y %H:%M",
)


def parse_date_value(value: str | None) -> date | None:
    if value is None:
        return None

    cleaned = value.strip()
    if not cleaned:
        return None

    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(cleaned).date()
    except ValueError:
        return None


def parse_datetime_value(value: str | None) -> datetime | None:
    if value is None:
        return None

    cleaned = value.strip()
    if not cleaned:
        return None

    for fmt in DATETIME_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(cleaned)
    except ValueError:
        return None


def to_iso_date(value: str | None) -> str | None:
    parsed = parse_date_value(value)
    return parsed.isoformat() if parsed else None


def to_iso_datetime(value: str | None) -> str | None:
    parsed = parse_datetime_value(value)
    return parsed.isoformat() if parsed else None


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def split_date_windows(start: date, end: date, max_days: int = 365) -> list[tuple[date, date]]:
    windows: list[tuple[date, date]] = []
    current = start

    while current <= end:
        window_end = min(current + timedelta(days=max_days - 1), end)
        windows.append((current, window_end))
        current = window_end + timedelta(days=1)

    return windows
