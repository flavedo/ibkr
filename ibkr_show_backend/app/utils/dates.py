from datetime import date, timedelta


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def get_default_start_date(end_date: date, days: int = 90) -> date:
    return end_date - timedelta(days=days - 1)
