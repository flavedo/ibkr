from pydantic import BaseModel


class VixRange(BaseModel):
    label: str
    sentiment: str
    strategy: str
    color: str
    is_current: bool


class FearGreedRange(BaseModel):
    label: str
    sentiment: str
    strategy: str
    color: str
    is_current: bool


class MarketSentimentResponse(BaseModel):
    vix_value: float | None = None
    vix_level: str = ""
    vix_ranges: list[VixRange] = []
    fear_greed_value: int | None = None
    fear_greed_level: str = ""
    fear_greed_ranges: list[FearGreedRange] = []
