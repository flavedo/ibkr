from pydantic import BaseModel


class EarningsEvent(BaseModel):
    company: str
    marketcap: float | None = None
    event_name: str | None = None
    date_time: str | None = None
    timing: str | None = None
    eps_estimate: float | None = None
    reported_eps: float | None = None
    surprise_pct: float | None = None


class EarningsCalendarResponse(BaseModel):
    items: list[EarningsEvent]


class EconomicEvent(BaseModel):
    event_name: str | None = None
    region: str
    event_time: str | None = None
    for_period: str | None = None
    actual: float | None = None
    expected: float | None = None
    last: float | None = None
    revised: float | None = None


class EconomicCalendarResponse(BaseModel):
    items: list[EconomicEvent]
