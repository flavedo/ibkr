from pydantic import BaseModel

from app.schemas.common import PaginationInfo


class CashFlowItem(BaseModel):
    account_id: str
    currency: str | None = None
    description: str | None = None
    date_time: str | None = None
    settle_date: str | None = None
    available_for_trading_date: str | None = None
    amount: float | None = None
    flow_direction: str | None = None
    flow_type: str | None = None
    transaction_id: str | None = None
    report_date: str | None = None
    client_reference: str | None = None


class CashFlowListResponse(BaseModel):
    items: list[CashFlowItem]
    pagination: PaginationInfo


class CashFlowCurrencySummaryItem(BaseModel):
    currency: str | None = None
    record_count: int
    deposit_count: int
    withdrawal_count: int
    total_deposit_amount: float
    total_withdrawal_amount: float
    net_amount: float


class CashFlowSummaryResponse(BaseModel):
    record_count: int
    deposit_count: int
    withdrawal_count: int
    total_deposit_amount: float | None = None
    total_withdrawal_amount: float | None = None
    net_amount: float | None = None
    by_currency: list[CashFlowCurrencySummaryItem]
