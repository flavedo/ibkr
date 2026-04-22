from pydantic import BaseModel


class AccountDeltaMetric(BaseModel):
    amount_change: float | None = None
    percent_change: float | None = None


class AccountOverviewResponse(BaseModel):
    account_id: str
    report_date: str
    currency: str | None = None
    total_equity: float | None = None
    cash: float | None = None
    stock_value: float | None = None
    options_value: float | None = None
    funds_value: float | None = None
    crypto_value: float | None = None
    interest_accruals: float | None = None
    dividend_accruals: float | None = None
    margin_financing_charge_accruals: float | None = None
    fifo_total_realized_pnl: float | None = None
    fifo_total_unrealized_pnl: float | None = None
    fifo_total_pnl: float | None = None
    cnav_twr: float | None = None
    ytd_twr: float | None = None
    crtt_dividends_ytd: float | None = None
    crtt_broker_interest_ytd: float | None = None
    crtt_commissions_ytd: float | None = None
    total_equity_delta: AccountDeltaMetric | None = None
    fifo_total_realized_pnl_delta: AccountDeltaMetric | None = None
    fifo_total_unrealized_pnl_delta: AccountDeltaMetric | None = None
    fifo_total_pnl_delta: AccountDeltaMetric | None = None


class LatestReportDateResponse(BaseModel):
    report_date: str
