from pydantic import BaseModel

from app.schemas.common import PaginationInfo


class DividendItem(BaseModel):
    account_id: str
    currency: str | None = None
    symbol: str | None = None
    description: str | None = None
    date_time: str | None = None
    settle_date: str | None = None
    amount: float | None = None
    gross_amount: float | None = None
    tax: float | None = None
    fx_rate_to_base: float | None = None
    amount_in_base: float | None = None
    flow_direction: str | None = None
    flow_type: str | None = None
    dividend_type: str | None = None
    transaction_id: str | None = None
    report_date: str | None = None
    activity_code: str | None = None
    activity_description: str | None = None
    level_of_detail: str | None = None


class DividendListResponse(BaseModel):
    items: list[DividendItem]
    pagination: PaginationInfo


class DividendSummaryResponse(BaseModel):
    record_count: int
    total_amount: float | None = None
    total_gross_amount: float | None = None
    by_symbol: dict[str, float]