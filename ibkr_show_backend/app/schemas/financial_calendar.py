from pydantic import BaseModel


class EarningsEvent(BaseModel):
    symbol: str = ""
    name: str = ""
    mcap: float = 0
    exchange: str = ""
    date: str = ""
    is_estimate: bool = True
    eps_avg: float | None = None
    eps_low: float | None = None
    eps_high: float | None = None
    rev_avg: float | None = None
    rev_low: float | None = None
    rev_high: float | None = None
    call_date: str = ""


class EarningsCalendarResponse(BaseModel):
    items: list[EarningsEvent]


class MacroEvent(BaseModel):
    date: str = ""
    title: str = ""
    type: str = "other"
    importance: str = "low"
    description: str = ""
    time: str | None = None
    actual: str | None = None
    expected: str | None = None
    previous: str | None = None


class MacroEventResponse(BaseModel):
    items: list[MacroEvent]
